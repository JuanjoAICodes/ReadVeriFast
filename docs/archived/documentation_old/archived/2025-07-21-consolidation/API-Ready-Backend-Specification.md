# VeriFast - API-Ready Backend Specification

*Created: July 17, 2025*

## 🎯 **Purpose**
This document outlines the API-ready backend architecture for VeriFast, designed to support both the current web application and future mobile applications (Android/iOS).

## 📱 **Mobile App Support Strategy**

### **Current Status**
- ✅ **Django Backend**: Fully functional web application
- ✅ **DRF Foundation**: Django REST Framework installed and ready
- ⚠️ **API Endpoints**: Need to be implemented
- ⚠️ **API Authentication**: Need to be configured
- ⚠️ **API Documentation**: Need to be created

### **Architecture Approach**
The backend follows a **dual-interface pattern**:
1. **Web Interface**: Django templates for browser users
2. **API Interface**: JSON REST API for mobile apps

## 🏗️ **API Architecture Design**

### **1. API Endpoints Structure**

#### **Authentication Endpoints**
```
POST /api/auth/register/          - User registration
POST /api/auth/login/             - User login (token-based)
POST /api/auth/logout/            - User logout
POST /api/auth/refresh/           - Token refresh
GET  /api/auth/profile/           - Get user profile
PUT  /api/auth/profile/           - Update user profile
```

#### **Article Endpoints**
```
GET    /api/articles/             - List articles (paginated)
GET    /api/articles/{id}/        - Get article details
POST   /api/articles/             - Submit article URL
GET    /api/articles/{id}/quiz/   - Get quiz data
POST   /api/articles/{id}/quiz/   - Submit quiz attempt
```

#### **Speed Reader Endpoints**
```
GET    /api/articles/{id}/content/    - Get processed content for speed reader
POST   /api/reading-sessions/         - Start reading session
PUT    /api/reading-sessions/{id}/    - Update reading progress
POST   /api/reading-sessions/{id}/complete/ - Complete reading session
```

#### **Social Features Endpoints**
```
GET    /api/articles/{id}/comments/           - Get comments
POST   /api/articles/{id}/comments/           - Post comment
POST   /api/comments/{id}/interact/           - Interact with comment
GET    /api/users/{id}/stats/                 - Get user statistics
```

#### **Gamification Endpoints**
```
GET    /api/users/me/xp/                      - Get XP details
GET    /api/users/me/achievements/            - Get achievements
GET    /api/leaderboard/                      - Get leaderboard
POST   /api/users/me/wpm/                     - Update WPM settings
```

### **2. API Response Format**

#### **Standard Success Response**
```json
{
  "success": true,
  "data": {
    // Response data here
  },
  "meta": {
    "timestamp": "2025-07-17T10:30:00Z",
    "version": "1.0"
  }
}
```

#### **Standard Error Response**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field_name": ["This field is required"]
    }
  },
  "meta": {
    "timestamp": "2025-07-17T10:30:00Z",
    "version": "1.0"
  }
}
```

#### **Paginated Response**
```json
{
  "success": true,
  "data": {
    "results": [...],
    "pagination": {
      "count": 150,
      "next": "/api/articles/?page=3",
      "previous": "/api/articles/?page=1",
      "page_size": 20,
      "current_page": 2,
      "total_pages": 8
    }
  }
}
```

### **3. Authentication Strategy**

#### **Token-Based Authentication**
- **JWT Tokens**: For stateless authentication
- **Refresh Tokens**: For secure token renewal
- **Token Expiry**: 24 hours for access tokens, 7 days for refresh tokens

#### **Permission Levels**
```python
# Permission classes for different endpoints
- AllowAny: Public article listing
- IsAuthenticated: User profile, quiz attempts
- IsOwnerOrReadOnly: User's own data
- IsAdminUser: Admin-only endpoints
```

### **4. Data Serialization**

#### **Article Serializer**
```python
class ArticleSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    quiz_available = serializers.SerializerMethodField()
    
    class Meta:
        model = Article
        fields = [
            'id', 'title', 'content', 'image_url', 
            'source', 'publication_date', 'reading_level',
            'tags', 'quiz_available'
        ]
    
    def get_quiz_available(self, obj):
        return bool(obj.quiz_data)
```

#### **User Profile Serializer**
```python
class UserProfileSerializer(serializers.ModelSerializer):
    stats = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'current_wpm', 'max_wpm',
            'total_xp', 'current_xp_points', 'preferred_language',
            'theme', 'stats'
        ]
        read_only_fields = ['id', 'total_xp']
    
    def get_stats(self, obj):
        return {
            'articles_read': QuizAttempt.objects.filter(user=obj, score__gte=60).count(),
            'average_score': obj.get_average_quiz_score(),
            'reading_streak': obj.get_reading_streak()
        }
```

## 🔧 **Implementation Plan**

### **Phase 1: Core API Setup (Week 1)**
1. **DRF Configuration**
   - Configure Django REST Framework settings
   - Set up API routing structure
   - Implement base serializers

2. **Authentication System**
   - JWT token authentication
   - User registration/login endpoints
   - Profile management endpoints

3. **Article API**
   - Article listing and detail endpoints
   - Content delivery for speed reader
   - Basic CRUD operations

### **Phase 2: Advanced Features (Week 2)**
1. **Quiz System API**
   - Quiz data delivery
   - Quiz attempt submission
   - Score calculation and XP rewards

2. **Social Features API**
   - Comment system endpoints
   - User interaction endpoints
   - Statistics and leaderboard

3. **Speed Reader API**
   - Reading session management
   - Progress tracking
   - WPM settings synchronization

### **Phase 3: Polish & Documentation (Week 3)**
1. **API Documentation**
   - Swagger/OpenAPI documentation
   - Interactive API explorer
   - Mobile developer guides

2. **Testing & Optimization**
   - API endpoint testing
   - Performance optimization
   - Rate limiting implementation

3. **Mobile App Preparation**
   - API client libraries
   - Authentication flow documentation
   - Data synchronization strategies

## 📱 **Mobile App Integration Strategy**

### **Data Synchronization**
- **Online Mode**: Real-time API calls
- **Offline Mode**: Local storage with sync when online
- **Conflict Resolution**: Last-write-wins with user notification

### **Authentication Flow**
1. User logs in via mobile app
2. App receives JWT tokens
3. Tokens stored securely on device
4. API calls include Authorization header
5. Automatic token refresh when needed

### **Speed Reader Mobile Optimization**
- **Chunked Content Delivery**: Optimized for mobile bandwidth
- **Progress Synchronization**: Real-time reading progress sync
- **Offline Reading**: Download articles for offline reading

## 🔒 **Security Considerations**

### **API Security**
- **HTTPS Only**: All API communication over HTTPS
- **Rate Limiting**: Prevent API abuse
- **Input Validation**: Comprehensive request validation
- **CORS Configuration**: Proper cross-origin settings

### **Authentication Security**
- **Token Rotation**: Regular token refresh
- **Secure Storage**: Encrypted token storage on mobile
- **Session Management**: Proper logout and cleanup
- **Brute Force Protection**: Login attempt limiting

## 📊 **Performance Optimization**

### **API Performance**
- **Database Optimization**: Efficient queries with select_related/prefetch_related
- **Caching Strategy**: Redis caching for frequently accessed data
- **Pagination**: Efficient pagination for large datasets
- **Response Compression**: Gzip compression for API responses

### **Mobile Optimization**
- **Minimal Payloads**: Only send necessary data
- **Image Optimization**: Compressed images for mobile
- **Lazy Loading**: Load content as needed
- **Background Sync**: Sync data in background

## 🧪 **Testing Strategy**

### **API Testing**
```python
# Example API test
class ArticleAPITestCase(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_article_list(self):
        response = self.client.get('/api/articles/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
    
    def test_quiz_submission(self):
        article = Article.objects.create(title='Test Article')
        data = {
            'score_percentage': 85.0,
            'wpm_used': 300,
            'quiz_time_seconds': 120
        }
        response = self.client.post(f'/api/articles/{article.id}/quiz/', data)
        self.assertEqual(response.status_code, 201)
```

## 📚 **Documentation Requirements**

### **API Documentation**
- **OpenAPI/Swagger**: Interactive API documentation
- **Postman Collection**: Ready-to-use API collection
- **Code Examples**: Sample requests/responses in multiple languages
- **Authentication Guide**: Step-by-step auth implementation

### **Mobile Developer Guide**
- **Getting Started**: Quick start guide for mobile developers
- **Authentication Flow**: Detailed auth implementation
- **Data Models**: Complete data structure documentation
- **Error Handling**: Comprehensive error code reference

## 🎯 **Success Metrics**

### **API Performance Metrics**
- **Response Time**: < 200ms for 95% of requests
- **Uptime**: 99.9% availability
- **Throughput**: Support 1000+ concurrent users
- **Error Rate**: < 1% error rate

### **Mobile App Readiness**
- **Complete API Coverage**: All web features available via API
- **Documentation Quality**: Comprehensive developer documentation
- **Testing Coverage**: 90%+ API test coverage
- **Performance**: Optimized for mobile bandwidth

---

*This specification ensures VeriFast backend is fully prepared for mobile app development while maintaining the current web application functionality.*