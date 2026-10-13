"""知识分类服务"""
from sqlalchemy.orm import Session

from app.models.category import Category


def create_category(db: Session, name: str, parent_id: int = 0, sort: int = 0) -> Category:
    c = Category(name=name, parent_id=parent_id, sort=sort)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


def list_categories(db: Session) -> list[Category]:
    return db.query(Category).order_by(Category.parent_id, Category.sort).all()


def update_category(db: Session, category_id: int, name: str | None = None,
                    parent_id: int | None = None, sort: int | None = None) -> Category:
    c = db.get(Category, category_id)
    if not c:
        raise ValueError("分类不存在")
    if name is not None:
        c.name = name
    if parent_id is not None:
        c.parent_id = parent_id
    if sort is not None:
        c.sort = sort
    db.commit()
    db.refresh(c)
    return c


def delete_category(db: Session, category_id: int) -> None:
    c = db.get(Category, category_id)
    if not c:
        raise ValueError("分类不存在")
    db.delete(c)
    db.commit()
