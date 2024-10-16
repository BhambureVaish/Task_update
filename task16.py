import os
import logging
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, EmailStr, validator
from sqlalchemy import create_engine, Column, Integer, BigInteger, String, TIMESTAMP, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
from dotenv import load_dotenv
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
import jwt
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Database URL from .env file
DATABASE_URL = os.getenv("DATABASE_URL")

# SQLAlchemy setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Email configuration
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",  # Update if you're using a different email provider
    MAIL_FROM_NAME="Your Company Name",
    MAIL_TLS=True,
    MAIL_SSL=False,
)

# User model
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, index=True)
    last_name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    phone_number = Column(BigInteger, unique=True, index=True)
    password = Column(String)
    created_at = Column(TIMESTAMP, server_default=func.now())
    reset_token = Column(String, nullable=True)
    reset_token_expires = Column(TIMESTAMP, nullable=True)

# Create the table if it doesn't exist
Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI()

class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str  # Keep it as a string for validation
    password: str

    @validator('phone_number')
    def validate_phone_number(cls, v):
        if not v.isdigit() or not (10 <= len(v) <= 15):
            raise ValueError('Phone number must be numeric and between 10 to 15 digits long')
        return int(v)  # Convert to integer for storage

@app.post("/register")
def register(user: UserCreate):
    db = SessionLocal()
    hashed_password = pwd_context.hash(user.password)

    try:
        logger.info("Checking for existing email or phone number...")
        # Check if email or phone number already exists
        if db.query(User).filter((User.email == user.email) | (User.phone_number == int(user.phone_number))).first():
            logger.warning("Email or Phone Number already registered.")
            raise HTTPException(status_code=400, detail="Email or Phone Number already registered")

        logger.info("Creating new user...")
        new_user = User(
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            phone_number=int(user.phone_number),  # Store as integer
            password=hashed_password
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        logger.info("User registered successfully.")
        return {"message": "User registered successfully"}
    except HTTPException as e:
        logger.error(f"HTTP Exception occurred: {e.detail}")
        raise
    except Exception as e:
        db.rollback()  # Rollback on error
        logger.error(f"Unexpected error during registration: {e}")
        raise HTTPException(status_code=500, detail="An error occurred during registration.")
    finally:
        db.close()

@app.post("/login")
def login(email: EmailStr, password: str):
    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()

    if not user:
        db.close()
        logger.warning("Email not found.")
        raise HTTPException(status_code=400, detail="Email not found")

    if not pwd_context.verify(password, user.password):
        db.close()
        logger.warning("Invalid password.")
        raise HTTPException(status_code=400, detail="Invalid password")

    db.close()
    logger.info("Login successful.")
    return {"message": "Login successful"}

@app.post("/forgot-password")
async def forgot_password(email: EmailStr, background_tasks: BackgroundTasks):
    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()

    if not user:
        db.close()
        logger.warning("Email not found.")
        raise HTTPException(status_code=404, detail="Email not found")

    # Create a JWT token
    token = jwt.encode(
        {"email": user.email, "exp": datetime.utcnow() + timedelta(hours=1)},
        os.getenv("SECRET_KEY"),
        algorithm="HS256"
    )

    # Update user's reset token and expiration
    user.reset_token = token
    user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
    db.commit()

    # Send email
    message = MessageSchema(
        subject="Password Reset Request",
        recipients=[user.email],
        body=f"Your password reset link: http://yourfrontend.com/reset-password?token={token}",
        subtype="html"
    )
    fm = FastMail(conf)
    background_tasks.add_task(fm.send_message, message)

    db.close()
    return {"message": "Password reset email sent"}

@app.post("/reset-password")
def reset_password(token: str, new_password: str):
    db = SessionLocal()
    
    try:
        # Decode the JWT token
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=["HS256"])
        email = payload.get("email")
        
        user = db.query(User).filter(User.email == email).first()

        if not user:
            raise HTTPException(status_code=400, detail="Invalid token")

        # Update password
        hashed_password = pwd_context.hash(new_password)
        user.password = hashed_password
        db.commit()
        
        logger.info("Password reset successfully.")
        return {"message": "Password reset successfully"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=400, detail="Invalid token")
    finally:
        db.close()


@app.get("/")
def read_root():
    return {"message": "Welcome to the User Management System"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
