from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm

from models import User
from schemas import UserCreate, UserResponse, TokenResponse, document_to_response
from database import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter()


# ============================================================
# POST /auth/register
#
# Creates a new user account.
# Steps:
#   1. Check username and email are not already taken
#   2. Hash the password (never store plain text)
#   3. Save the User document to MongoDB
#   4. Return the created user (without password)
# ============================================================

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(body: UserCreate):
    # Check for duplicate username
    existing = await User.find_one(User.username == body.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )

    # Check for duplicate email
    existing = await User.find_one(User.email == body.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create and save the new user
    new_user = User(
        username=body.username,
        email=body.email,
        hashed_password=hash_password(body.password),
    )
    await new_user.insert()

    return document_to_response(new_user, UserResponse)


# ============================================================
# POST /auth/login
#
# Authenticates a user and returns a JWT access token.
#
# We use OAuth2PasswordRequestForm (not our UserLogin schema)
# because this is the standard OAuth2 form format that
# Swagger UI (/docs) understands for the "Authorize" button.
# The form sends `username` and `password` as form fields.
# We treat `username` as email here.
# ============================================================

@router.post("/login", response_model=TokenResponse)
async def login(form: OAuth2PasswordRequestForm = Depends()):
    # Sử dụng toán tử $or của MongoDB
    user = await User.find_one({
        "$or": [
            {"email": form.username},
            {"username": form.username}
        ]
    })

    token = create_access_token(data={"sub": str(user.id)})
    return TokenResponse(access_token=token, token_type="bearer")

# ============================================================
# GET /auth/me
#
# Returns the currently logged-in user's profile.
# Depends(get_current_user) validates the JWT automatically.
# ============================================================

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return document_to_response(current_user, UserResponse)