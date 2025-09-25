# routers/content.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import MaterialTable
from schemas import UnitWithThemes

router = APIRouter(prefix="/content", tags=["content"])

@router.get("/{material_name}", response_model=list[UnitWithThemes])
def get_material_content(material_name: str, db: Session = Depends(get_db)):
    """
    例: GET /content/高校１年生_物理基礎
    紐づく units -> lesson_themes -> lecture_videos をネストして返す（教材名で検索）
    """
    material = db.query(MaterialTable)\
                .filter(MaterialTable.material_name == material_name)\
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
    material = db.query(MaterialTable)\
                .filter(MaterialTable.material_id == material_id)\
                .first()
    
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    # models.pyのrelationshipにより、material.unitsからさらにlesson_themes -> lecture_videosとたどれる
    return material.units