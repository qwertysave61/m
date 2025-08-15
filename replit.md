# RiseBuilder - Telegram Bot Factory Platform

## Overview

RiseBuilder is a comprehensive Telegram bot creation platform that enables users to create and deploy custom Telegram bots without coding knowledge. The platform provides a template-based system with multiple bot categories including business, utility, social, and professional bots. Users can select from pre-built templates, configure them through an intuitive interface, and deploy fully functional bots with built-in analytics, payment processing, and monitoring capabilities.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **FastAPI Framework**: Core web API built with FastAPI for high-performance async operations
- **Aiogram Integration**: Primary Telegram bot framework for handling bot interactions and messaging
- **Async SQLAlchemy**: Database ORM with async support for efficient database operations
- **Celery Task Queue**: Background task processing for payment checking, bot monitoring, and cleanup operations
- **Redis**: Used as message broker for Celery and FSM (Finite State Machine) storage

### Database Design
- **PostgreSQL**: Primary database for storing users, bots, templates, payments, and analytics
- **SQLite**: Used within individual bot instances for template-specific data storage
- **Model Structure**: Comprehensive models including User, Bot, BotTemplate, Payment, SystemSettings with proper relationships

### Bot Factory System
- **Template Engine**: Pre-built bot templates in categories (echo, e-commerce, restaurant, quiz, weather, etc.)
- **Dynamic Deployment**: Automated bot creation, code generation, and process management
- **Configuration Schema**: JSON-based configuration system for customizing bot behavior
- **Process Management**: Individual Python processes for each deployed bot with health monitoring

### Payment and Billing
- **Subscription Model**: Daily fee structure for running bots with creation fees
- **Balance System**: User wallet system with automatic payment processing
- **Payment Notifications**: Multi-stage warning system before bot suspension
- **Cleanup Service**: Automated cleanup of suspended bots after grace period

### Monitoring and Analytics
- **Health Monitoring**: Real-time bot status checking and automatic restart capabilities
- **Performance Analytics**: Message counts, user activity, uptime tracking
- **System Monitoring**: Resource usage and performance metrics
- **Notification System**: Automated alerts for low balance, bot failures, and system issues

### File Management
- **Bot Storage**: Organized file structure for each deployed bot instance
- **Template System**: Standardized template structure with code and configuration files
- **Upload Handling**: File upload system for bot customization and media handling
- **Cleanup Automation**: Scheduled cleanup of old files and unused bot instances

### Security and Administration
- **Admin Panel**: Comprehensive admin interface for user management, template management, and system monitoring
- **Role-based Access**: Admin and user roles with appropriate permissions
- **Data Validation**: Input validation for bot tokens, usernames, and configuration data
- **Error Handling**: Comprehensive error logging and graceful failure handling

## External Dependencies

### Core Infrastructure
- **PostgreSQL Database**: Primary data storage with async connection pooling
- **Redis Server**: Message broker and caching layer for Celery and FSM storage
- **Telegram Bot API**: Core platform for bot communication and management

### Payment Processing
- **Telegram Payments**: Integrated payment provider for subscription billing
- **Payment Provider Token**: External payment gateway integration

### External APIs
- **Weather API**: OpenWeatherMap integration for weather bot templates
- **Currency API**: Exchange rate data for financial bot templates
- **File Processing Libraries**: PIL, FFmpeg for media conversion and processing

### Development Tools
- **Loguru**: Advanced logging with rotation and structured output
- **Pydantic**: Data validation and settings management
- **Aiofiles**: Async file operations for bot deployment
- **Aiogram**: Modern Telegram Bot API framework

### Template Dependencies
- **SQLite**: Local database for individual bot instances
- **Aiohttp**: HTTP client for external API calls within bots
- **Various Python Libraries**: Template-specific dependencies (PIL for image processing, etc.)

### Monitoring and Maintenance
- **Psutil**: System resource monitoring
- **Background Tasks**: Celery workers for automated maintenance
- **File System Management**: Automated cleanup and organization
- **Health Check Systems**: Automated bot health monitoring and restart capabilities