"""
Tests for the FastAPI application endpoints
"""
from fastapi import status


class TestBasicRoutes:
    """Test basic application routes"""
    
    def test_root_redirect(self, client):
        """Test that root redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        assert "/static/index.html" in response.headers["location"]


class TestActivitiesEndpoint:
    """Test the activities endpoint"""
    
    def test_get_activities(self, client, reset_activities):
        """Test getting all activities"""
        response = client.get("/activities")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        
        # Check structure of an activity
        chess_club = data["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)
    
    def test_activities_have_correct_structure(self, client, reset_activities):
        """Test that all activities have the required structure"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["max_participants"], int)
            assert isinstance(activity_data["participants"], list)


class TestSignupEndpoint:
    """Test the signup functionality"""
    
    def test_successful_signup(self, client, reset_activities):
        """Test successful student signup"""
        email = "newstudent@mergington.edu"
        activity = "Chess Club"
        
        # Get initial participant count
        initial_response = client.get("/activities")
        initial_participants = len(initial_response.json()[activity]["participants"])
        
        # Sign up
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity in data["message"]
        
        # Verify participant was added
        updated_response = client.get("/activities")
        updated_participants = updated_response.json()[activity]["participants"]
        assert len(updated_participants) == initial_participants + 1
        assert email in updated_participants
    
    def test_signup_for_nonexistent_activity(self, client, reset_activities):
        """Test signup for activity that doesn't exist"""
        email = "student@mergington.edu"
        activity = "Nonexistent Activity"
        
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        data = response.json()
        assert "detail" in data
        assert "Activity not found" in data["detail"]
    
    def test_duplicate_signup_prevention(self, client, reset_activities):
        """Test that students cannot sign up for multiple activities"""
        email = "student@mergington.edu"
        
        # Sign up for first activity
        response1 = client.post(f"/activities/Chess Club/signup?email={email}")
        assert response1.status_code == status.HTTP_200_OK
        
        # Try to sign up for second activity
        response2 = client.post(f"/activities/Programming Class/signup?email={email}")
        assert response2.status_code == status.HTTP_400_BAD_REQUEST
        
        data = response2.json()
        assert "detail" in data
        assert "already signed up" in data["detail"].lower()
    
    def test_signup_when_activity_is_full(self, client, reset_activities):
        """Test that students cannot sign up when activity is at max capacity"""
        activity = "Chess Club"
        
        # Get initial state
        initial_response = client.get("/activities")
        initial_data = initial_response.json()[activity]
        max_participants = initial_data["max_participants"]
        current_participants = len(initial_data["participants"])
        
        # Fill up the activity to max capacity
        spots_remaining = max_participants - current_participants
        for i in range(spots_remaining):
            email = f"student{i}@mergington.edu"
            response = client.post(f"/activities/{activity}/signup?email={email}")
            assert response.status_code == status.HTTP_200_OK
        
        # Verify activity is now full
        after_fill = client.get("/activities")
        assert len(after_fill.json()[activity]["participants"]) == max_participants
        
        # Try to sign up one more student (should fail)
        overflow_email = "overflow@mergington.edu"
        response = client.post(f"/activities/{activity}/signup?email={overflow_email}")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        data = response.json()
        assert "detail" in data
        assert "full" in data["detail"].lower()


class TestUnregisterEndpoint:
    """Test the unregister functionality"""
    
    def test_successful_unregister(self, client, reset_activities):
        """Test successful participant removal"""
        # Use existing participant
        email = "michael@mergington.edu"
        activity = "Chess Club"
        
        # Get initial participant count
        initial_response = client.get("/activities")
        initial_participants = initial_response.json()[activity]["participants"]
        assert email in initial_participants
        
        # Unregister
        response = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity in data["message"]
        
        # Verify participant was removed
        updated_response = client.get("/activities")
        updated_participants = updated_response.json()[activity]["participants"]
        assert email not in updated_participants
        assert len(updated_participants) == len(initial_participants) - 1
    
    def test_unregister_from_nonexistent_activity(self, client, reset_activities):
        """Test unregister from activity that doesn't exist"""
        email = "student@mergington.edu"
        activity = "Nonexistent Activity"
        
        response = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        data = response.json()
        assert "detail" in data
        assert "Activity not found" in data["detail"]
    
    def test_unregister_non_participant(self, client, reset_activities):
        """Test unregistering a student who isn't registered"""
        email = "nonparticipant@mergington.edu"
        activity = "Chess Club"
        
        response = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        data = response.json()
        assert "detail" in data
        assert "not registered" in data["detail"].lower()


class TestWorkflow:
    """Test complete signup and unregister workflow"""
    
    def test_complete_workflow(self, client, reset_activities):
        """Test complete signup -> unregister workflow"""
        email = "workflow@mergington.edu"
        activity = "Art Club"
        
        # Initial check - student not registered
        initial_response = client.get("/activities")
        initial_participants = initial_response.json()[activity]["participants"]
        assert email not in initial_participants
        
        # Sign up
        signup_response = client.post(f"/activities/{activity}/signup?email={email}")
        assert signup_response.status_code == status.HTTP_200_OK
        
        # Verify signup
        after_signup = client.get("/activities")
        after_signup_participants = after_signup.json()[activity]["participants"]
        assert email in after_signup_participants
        
        # Unregister
        unregister_response = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert unregister_response.status_code == status.HTTP_200_OK
        
        # Verify unregistration
        final_response = client.get("/activities")
        final_participants = final_response.json()[activity]["participants"]
        assert email not in final_participants
        assert len(final_participants) == len(initial_participants)