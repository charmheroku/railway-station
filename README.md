# Railway Station Booking System API 🚆

A robust, API for a train ticket booking system for reservation experiences across European railway networks.

## 🌟 [Live Demo API](https://railway-station.onrender.com/api/docs/)

Try out the API with these test credentials:
- Regular user: `john.doe@example.com` / `john.doe`
- Admin user: `admin@example.com` / `1`

## 📱 [Frontend Application](https://railway-station-front-frbs.vercel.app)

Experience the complete booking flow through user-friendly interface:
- Search for trips between cities
- View train schedules and available seats
- Select different wagon types (Economy/Lux)
- Book tickets for multiple passengers
- Manage your bookings

## 🔎 Search for trips between cities with filters
![image](https://github.com/user-attachments/assets/800c6b12-5404-4a75-86ca-230583cef642)
![image](https://github.com/user-attachments/assets/95f318e9-8048-4c43-a958-7affc6bff26a)

## ✔ View train schedules and available seats
![image](https://github.com/user-attachments/assets/8f5e75d2-0840-4e8c-8ace-9917d79f1f70)

## 🚎 Select different wagon types (Economy/Lux) and seats for different types of passengers
![image](https://github.com/user-attachments/assets/d1fadbd7-8fff-4a24-9d40-1080649e71ae)
![image](https://github.com/user-attachments/assets/ec491e48-de83-4345-a183-286880d5eb53)

## 👨‍👩‍👧‍👦 Book tickets for multiple passengers
![image](https://github.com/user-attachments/assets/b828e687-1710-4bf3-b013-3015670f9981)

## Manage your bookings
![image](https://github.com/user-attachments/assets/3603408c-00a1-4b4f-9653-962b76f9d3cb)

## Admin Dashboard

A clean, intuitive admin front interface for complete system management:

- **Stations & Routes**: Manage railway stations
- **Trains & Wagons**: Configure train types, wagons, and seating arrangements
- **Trips**: Schedule journeys with pricing and availability
- **Amenities**: Define comfort features available on different wagon types
- **Passenger Types**: Set up passenger categories with discount rules

The admin panel provides full CRUD operations for all system entities through a user-friendly dashboard with clear navigation and consistent design.
![image](https://github.com/user-attachments/assets/cdf94fff-5065-4e69-8ce7-8b28bd393dbb)
![image](https://github.com/user-attachments/assets/2755457c-3d4a-4f73-a9de-ea146b331d88)

## 🛠️ Tech Stack

### Backend
- **Python 3.11** with **Django 5.1**
- **Django REST Framework** for RESTful API implementation
- **PostgreSQL** for reliable data storage
- **JWT Authentication** for secure user sessions
- **Whitenoise** for efficient static files serving
- **Gunicorn** for production deployment
- **drf-spectacular** for OpenAPI/Swagger documentation

### Testing
- Comprehensive test suite for core business logic

## 🏗️ System Architecture

**DB architecture**
![image](https://github.com/user-attachments/assets/0522e611-7850-43da-a6bc-2b7b71961335)


The system follows architecture pattern with:
- **Models**: Train, Station, Route, Trip, Wagon, Booking, Ticket, etc.
- **APIs**: RESTful endpoints with proper permissions
- **Services**: Business logic isolated in service classes
- **Serializers**: Data validation and transformation

## 🔑 Key Features

### 🚉 Station & Route Management
- Store information about stations across Europe
- Define routes between stations with distances

### 🚋 Train & Wagon Configuration
- Configure different train types
- Manage wagon types with various amenities and pricing

### 🗓️ Trip Scheduling
- Create and manage trips with departure/arrival times
- Set base prices for different routes

### 🎫 Dynamic Booking System
- Real-time seat availability checking
- Price calculation based on passenger type and wagon class
- Discount management for different passenger categories

### 👤 User Management
- JWT-based authentication
- Role-based access control (passengers vs administrators)

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- PostgreSQL

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/railway-station.git
cd railway-station

# Set up virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables (copy from .env.example)
cp .env.example .env

# Run migrations
python manage.py migrate

# Load initial data
python manage.py loaddata fixtures.json

# Start the development server
python manage.py runserver
```

## 🧪 Running Tests

```bash
python manage.py test
```
