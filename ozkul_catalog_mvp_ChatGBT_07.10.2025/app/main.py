import os
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from .database import Base, engine, SessionLocal
from . import models, schemas
from .importer import import_from_excel
from .pdfgen import build_catalog
import tempfile
from jinja2 import Environment, FileSystemLoader

APP_TITLE = os.getenv("APP_TITLE", "Ozkul Catalog")
SECRET_PASSWORD = os.getenv("SECRET_PASSWORD", "ozkul123")
ALLOW_LOGO = os.getenv("ALLOW_LOGO", "true").lower() == "true"
ALLOW_COMPANY_NAME = os.getenv("ALLOW_COMPANY_NAME", "true").lower() == "true"
COMPANY_NAME = os.getenv("COMPANY_NAME", "ÖZKUL ELEKTRONİK")

app = FastAPI(title=APP_TITLE)
Base.metadata.create_all(bind=engine)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
templates = Environment(loader=FileSystemLoader("app/templates"))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_password(pw: str):
    if pw != SECRET_PASSWORD:
        raise HTTPException(status_code=401, detail="Şifre hatalı")

@app.get("/", response_class=HTMLResponse)
def home():
    return f"""
    <html><head><title>{APP_TITLE}</title></head>
    <body style='font-family:sans-serif;max-width:980px;margin:20px auto'>
      <h2>{APP_TITLE}</h2>
      <form action='/login' method='post'>
        <input type='password' name='pw' placeholder='Şifre' autofocus />
        <button type='submit'>Giriş</button>
      </form>
    </body></html>
    """

@app.post("/login")
def login(pw: str = Form(...)):
    if pw != SECRET_PASSWORD:
        return HTMLResponse("<p>Şifre yanlış.</p><a href='/'>Geri</a>", status_code=401)
    resp = RedirectResponse(url="/app", status_code=302)
    resp.set_cookie("auth", SECRET_PASSWORD, httponly=True, samesite="lax")
    return resp

def require_auth(auth: Optional[str] = None):
    # dummy dependency for brevity; cookie check in routes
    pass

def is_auth(request):
    return request.cookies.get("auth") == SECRET_PASSWORD

@app.get("/app", response_class=HTMLResponse)
def app_ui():
    html = templates.get_template("app.html").render(title=APP_TITLE)
    return HTMLResponse(html)

# API
from fastapi import Request

@app.get("/api/products", response_model=List[schemas.ProductOut])
def list_products(request: Request, q: Optional[str] = None, db: Session = Depends(get_db)):
    if not is_auth(request):
        raise HTTPException(401, "Yetkisiz")
    query = db.query(models.Product)
    if q:
        like = f"%{q}%"
        query = query.filter((models.Product.name.ilike(like)) | (models.Product.sku.ilike(like)))
    items = query.order_by(models.Product.created_at.desc()).limit(500).all()
    out = []
    for p in items:
        out.append(schemas.ProductOut(
            id=p.id, sku=p.sku, name=p.name, description=p.description, price=p.price,
            images=[schemas.ProductImageOut(id=im.id, path=f"/uploads/{os.path.basename(im.path)}", alt=im.alt, sort_order=im.sort_order) for im in p.images]
        ))
    return out

@app.post("/api/products", response_model=schemas.ProductOut)
def create_product(request: Request, p: schemas.ProductIn, db: Session = Depends(get_db)):
    if not is_auth(request):
        raise HTTPException(401, "Yetkisiz")
    obj = models.Product(sku=p.sku, name=p.name, description=p.description, price=p.price)
    db.add(obj); db.commit(); db.refresh(obj)
    return schemas.ProductOut(id=obj.id, **p.model_dump(), images=[])

@app.delete("/api/products/{pid}")
def delete_product(request: Request, pid: str, db: Session = Depends(get_db)):
    if not is_auth(request):
        raise HTTPException(401, "Yetkisiz")
    obj = db.get(models.Product, pid)
    if not obj: raise HTTPException(404, "Bulunamadı")
    db.delete(obj); db.commit()
    return {"ok": True}

@app.post("/api/import/excel")
def import_excel(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not is_auth(request):
        raise HTTPException(401, "Yetkisiz")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        tmp.write(file.file.read())
        tmp_path = tmp.name
    rows = import_from_excel(tmp_path, upload_dir="uploads")
    os.unlink(tmp_path)
    # upsert by SKU
    created, updated = 0, 0
    for r in rows:
        existing = db.query(models.Product).filter_by(sku=r['sku']).first()
        if existing:
            existing.name = r['name']; existing.description = r['description']; existing.price = r['price']
            # replace images
            for im in list(existing.images):
                db.delete(im)
            for idx, pth in enumerate(r['images']):
                db.add(models.ProductImage(product_id=existing.id, path=pth, sort_order=idx))
            updated += 1
        else:
            p = models.Product(sku=r['sku'], name=r['name'], description=r['description'], price=r['price'])
            db.add(p); db.flush()
            for idx, pth in enumerate(r['images']):
                db.add(models.ProductImage(product_id=p.id, path=pth, sort_order=idx))
            created += 1
    db.commit()
    return {"created": created, "updated": updated, "total": len(rows)}

from openpyxl import Workbook
@app.get("/api/export/excel")
def export_excel(request: Request, db: Session = Depends(get_db)):
    if not is_auth(request):
        raise HTTPException(401, "Yetkisiz")
    wb = Workbook(); ws = wb.active
    ws.append(["SKU","Name","Description","Price","ImagePaths"])  # images as paths list
    for p in db.query(models.Product).all():
        img_paths = ",".join([im.path for im in p.images])
        ws.append([p.sku, p.name, p.description or "", p.price if p.price is not None else "", img_paths])
    out = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx").name
    wb.save(out)
    return FileResponse(out, filename="ozkul_export.xlsx", media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@app.post("/api/catalog/pdf")
def catalog_pdf(request: Request, design: str = Form("classic"), show_logo: bool = Form(True), show_company: bool = Form(True)):
    if not is_auth(request):
        raise HTTPException(401, "Yetkisiz")
    # gather data
    from .database import SessionLocal
    db = SessionLocal()
    products = db.query(models.Product).all()
    rows = []
    for p in products:
        rows.append({
            'sku': p.sku,
            'name': p.name,
            'description': p.description,
            'price': p.price,
            'images': [im.path for im in sorted(p.images, key=lambda x: x.sort_order)]
        })
    out = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name
    logo_path = os.path.join("app","static","logo.png")
    build_catalog(out, rows, design=design, show_logo=show_logo, logo_path=logo_path if ALLOW_LOGO else None, show_company=show_company and ALLOW_COMPANY_NAME, company_name=COMPANY_NAME)
    return FileResponse(out, filename=f"ozkul_catalog_{design}.pdf", media_type="application/pdf")
