from fastapi import APIRouter, HTTPException, status, Depends
from beanie import PydanticObjectId

from models import Category, Task, User
from schemas import CategoryCreate, CategoryUpdate, CategoryResponse, document_to_response
from database import get_current_user

router = APIRouter()


# ============================================================
# Helper: fetch a category by ID and verify ownership
# ============================================================

async def get_category_or_raise(category_id: str, current_user: User) -> Category:
    try:
        object_id = PydanticObjectId(category_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid category ID format")

    category = await Category.get(object_id)

    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    if category.user_id != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return category


# ============================================================
# GET /categories
#
# Returns all categories belonging to the current user.
# ============================================================

@router.get("/", response_model=list[CategoryResponse])
async def get_categories(current_user: User = Depends(get_current_user)):
    categories = await Category.find(
        Category.user_id == str(current_user.id)
    ).sort(Category.name).to_list()

    return [document_to_response(c, CategoryResponse) for c in categories]


# ============================================================
# POST /categories
# ============================================================

@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    body:         CategoryCreate,
    current_user: User = Depends(get_current_user),
):
    # Prevent duplicate category names for the same user
    existing = await Category.find_one(
        Category.user_id == str(current_user.id),
        Category.name    == body.name,
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have a category with this name",
        )

    new_category = Category(
        user_id=str(current_user.id),
        name=body.name,
        color=body.color,
    )
    await new_category.insert()

    return document_to_response(new_category, CategoryResponse)


# ============================================================
# PATCH /categories/{category_id}
# ============================================================

@router.patch("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id:  str,
    body:         CategoryUpdate,
    current_user: User = Depends(get_current_user),
):
    category    = await get_category_or_raise(category_id, current_user)
    update_data = body.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided to update",
        )

    await category.set(update_data)
    return document_to_response(category, CategoryResponse)


# ============================================================
# DELETE /categories/{category_id}
#
# Deletes a category.
# Tasks that belonged to this category have their category_id
# set to None (they are NOT deleted along with the category).
# ============================================================

@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id:  str,
    current_user: User = Depends(get_current_user),
):
    category = await get_category_or_raise(category_id, current_user)

    # Unlink tasks from this category before deleting
    # (set category_id to None on all affected tasks)
    await Task.find(
        Task.user_id     == str(current_user.id),
        Task.category_id == category_id,
    ).set({Task.category_id: None})

    await category.delete()