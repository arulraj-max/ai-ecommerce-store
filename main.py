from fastapi import FastAPI, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import SessionLocal, engine
import models


# -----------------------
# APP INITIALIZATION
# -----------------------

app = FastAPI()

# Create database tables
models.Base.metadata.create_all(bind=engine)


# -----------------------
# STATIC + TEMPLATE SETUP
# -----------------------

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# -----------------------
# DATABASE DEPENDENCY
# -----------------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -----------------------
# ROUTES
# -----------------------

# HOME PAGE
@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, search: str = None, db: Session = Depends(get_db)):
    query = db.query(models.ProductModel)
    
    if search:
        query = query.filter(models.ProductModel.name.ilike(f"%{search}%"))
    
    products = query.all()
    product_count = len(products)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "items": products,
            "total": product_count,
            "search": search or ""
        }
    )


# ADD PRODUCT FROM UI
@app.post("/add-product")
def add_product(
    name: str = Form(...),
    price: float = Form(...),
    stock: int = Form(...),
    image_url: str = Form(None),
    db: Session = Depends(get_db)
):
    new_product = models.ProductModel(
        name=name,
        price=price,
        stock=stock,
        image_url=image_url
    )

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return RedirectResponse(url="/", status_code=303)


# DELETE PRODUCT FROM UI
@app.post("/delete/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.ProductModel).filter(
        models.ProductModel.id == product_id
    ).first()

    if product:
        db.delete(product)
        db.commit()

    return RedirectResponse(url="/", status_code=303)


# EDIT PRODUCT FROM UI
@app.post("/edit/{product_id}")
def edit_product(
    product_id: int,
    name: str = Form(...),
    price: float = Form(...),
    stock: int = Form(...),
    image_url: str = Form(None),
    db: Session = Depends(get_db)
):
    product = db.query(models.ProductModel).filter(
        models.ProductModel.id == product_id
    ).first()

    if product:
        product.name = name
        product.price = price
        product.stock = stock
        product.image_url = image_url
        db.commit()
    else:
        return RedirectResponse(url="/", status_code=303)

    return RedirectResponse(url="/", status_code=303)


# OPTIONAL API ENDPOINT (FOR TESTING)
@app.get("/items")
def get_items(db: Session = Depends(get_db)):
    return db.query(models.ProductModel).all()