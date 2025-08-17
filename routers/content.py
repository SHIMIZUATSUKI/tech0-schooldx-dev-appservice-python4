####### content.py

# 教材IDベースで取得するエンドポイントを追加
# 既存の GET /content/{material_name} は残したまま
# 新たに GET /content/by_id/{material_id} を追加しID指定で同じ構造を返す


from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import MaterialsTable
from schemas import UnitWithThemes

router = APIRouter(prefix="/content", tags=["content"])

@router.get("/{material_name}", response_model=list[UnitWithThemes])
def get_material_content(material_name: str, db: Session = Depends(get_db)):
    """
    例: GET /content/高校１年生_物理基礎
    紐づく units -> lesson_themes -> lecture_videos をネストして返す（教材名で検索）
    """
    material = db.query(MaterialsTable)\
                .filter(MaterialsTable.material_name == material_name)\
                .first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    # material.units -> UnitWithThemes によってネストされた形で返せる
    return material.units

@router.get("/by_id/{material_id}", response_model=list[UnitWithThemes])
def get_material_content_by_id(material_id: int, db: Session = Depends(get_db)):
    """
    例: GET /content/by_id/1
    紐づく units -> lesson_themes -> lecture_videos をネストして返す（教材IDで検索）
    """
    material = db.query(MaterialsTable)\
                .filter(MaterialsTable.material_id == material_id)\
                .first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    # models.pyのrelationshipにより、material.unitsからさらにlesson_themes -> lecture_videosとたどれる
    return material.units
