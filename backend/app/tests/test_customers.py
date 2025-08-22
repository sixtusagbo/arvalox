import pytest

from app.core.security import create_access_token, UserRole
from app.schemas.customer import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
    CustomerSearchParams,
    CustomerListResponse,
)


class TestCustomerSchemas:
    """Test customer Pydantic schemas"""

    def test_customer_create_valid(self):
        """Test valid customer creation schema"""
        customer_data = {
            "customer_code": "CUST001",
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "123-456-7890",
            "billing_address": "123 Main St",
            "shipping_address": "123 Main St",
            "credit_limit": 5000.0,
            "payment_terms": 30,
            "tax_id": "TAX123",
            "status": "active",
        }

        customer = CustomerCreate(**customer_data)
        assert customer.customer_code == "CUST001"
        assert customer.name == "John Doe"
        assert customer.email == "john@example.com"
        assert customer.status == "active"

    def test_customer_create_invalid_email(self):
        """Test customer creation with invalid email"""
        customer_data = {
            "customer_code": "CUST001",
            "name": "John Doe",
            "email": "invalid-email",
            "status": "active",
        }

        with pytest.raises(ValueError):
            CustomerCreate(**customer_data)

    def test_customer_create_invalid_status(self):
        """Test customer creation with invalid status"""
        customer_data = {
            "customer_code": "CUST001",
            "name": "John Doe",
            "status": "invalid_status",
        }

        with pytest.raises(ValueError):
            CustomerCreate(**customer_data)

    def test_customer_create_missing_required_fields(self):
        """Test customer creation with missing required fields"""
        customer_data = {
            "name": "John Doe"
            # Missing customer_code
        }

        with pytest.raises(ValueError):
            CustomerCreate(**customer_data)

    def test_customer_update_partial(self):
        """Test customer update with partial data"""
        update_data = {
            "name": "Updated Name",
            "email": "updated@example.com",
        }

        customer_update = CustomerUpdate(**update_data)
        assert customer_update.name == "Updated Name"
        assert customer_update.email == "updated@example.com"
        assert customer_update.customer_code is None  # Not provided

    def test_customer_response_schema(self):
        """Test customer response schema"""
        from datetime import datetime

        response_data = {
            "id": 1,
            "organization_id": 1,
            "customer_code": "CUST001",
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "123-456-7890",
            "billing_address": "123 Main St",
            "shipping_address": "123 Main St",
            "credit_limit": 5000.0,
            "payment_terms": 30,
            "tax_id": "TAX123",
            "status": "active",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

        customer_response = CustomerResponse(**response_data)
        assert customer_response.id == 1
        assert customer_response.organization_id == 1
        assert customer_response.customer_code == "CUST001"

    def test_customer_search_params_validation(self):
        """Test customer search parameters validation"""
        # Valid search params
        valid_params = {
            "search": "test",
            "status": "active",
            "payment_terms_min": 0,
            "payment_terms_max": 60,
            "has_credit_limit": True,
            "page": 1,
            "per_page": 20,
            "sort_by": "name",
            "sort_order": "asc",
        }

        search_params = CustomerSearchParams(**valid_params)
        assert search_params.search == "test"
        assert search_params.status == "active"
        assert search_params.page == 1
        assert search_params.per_page == 20

    def test_customer_search_params_invalid_status(self):
        """Test customer search with invalid status"""
        invalid_params = {"status": "invalid_status"}

        with pytest.raises(ValueError):
            CustomerSearchParams(**invalid_params)

    def test_customer_search_params_invalid_sort_order(self):
        """Test customer search with invalid sort order"""
        invalid_params = {"sort_order": "invalid_order"}

        with pytest.raises(ValueError):
            CustomerSearchParams(**invalid_params)

    def test_customer_list_response_schema(self):
        """Test customer list response schema"""
        from datetime import datetime

        customer_data = {
            "id": 1,
            "organization_id": 1,
            "customer_code": "CUST001",
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "123-456-7890",
            "billing_address": "123 Main St",
            "shipping_address": "123 Main St",
            "credit_limit": 5000.0,
            "payment_terms": 30,
            "tax_id": "TAX123",
            "status": "active",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

        list_response_data = {
            "customers": [customer_data],
            "total": 1,
            "page": 1,
            "per_page": 20,
            "total_pages": 1,
        }

        list_response = CustomerListResponse(**list_response_data)
        assert len(list_response.customers) == 1
        assert list_response.total == 1
        assert list_response.page == 1
        assert list_response.total_pages == 1


class TestCustomerBusinessLogic:
    """Test customer business logic without database"""

    def create_test_token(
        self, user_id: int = 1, organization_id: int = 1, role: str = "owner"
    ):
        """Helper to create test JWT token"""
        return create_access_token(
            user_id=user_id,
            organization_id=organization_id,
            email="test@example.com",
            role=role,
        )

    def test_jwt_token_creation(self):
        """Test JWT token creation for customer API"""
        token = self.create_test_token(
            user_id=1, organization_id=1, role="owner"
        )
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_jwt_token_different_organizations(self):
        """Test JWT tokens for different organizations"""
        token_org1 = self.create_test_token(user_id=1, organization_id=1)
        token_org2 = self.create_test_token(user_id=2, organization_id=2)

        assert token_org1 != token_org2

        # Verify token contents
        from app.core.security import verify_token

        payload1 = verify_token(token_org1)
        payload2 = verify_token(token_org2)

        assert payload1["organization_id"] == 1
        assert payload2["organization_id"] == 2
        assert payload1["sub"] == "1"
        assert payload2["sub"] == "2"

    def test_customer_validation_rules(self):
        """Test customer validation business rules"""
        # Test payment terms validation
        valid_customer = CustomerCreate(
            customer_code="VALID001",
            name="Valid Customer",
            payment_terms=30,
            status="active",
        )
        assert valid_customer.payment_terms == 30

        # Test invalid payment terms (negative)
        with pytest.raises(ValueError):
            CustomerCreate(
                customer_code="INVALID001",
                name="Invalid Customer",
                payment_terms=-1,
                status="active",
            )

        # Test invalid payment terms (too high)
        with pytest.raises(ValueError):
            CustomerCreate(
                customer_code="INVALID002",
                name="Invalid Customer",
                payment_terms=400,  # Max is 365
                status="active",
            )

    def test_customer_credit_limit_validation(self):
        """Test customer credit limit validation"""
        # Valid credit limit
        valid_customer = CustomerCreate(
            customer_code="CREDIT001",
            name="Credit Customer",
            credit_limit=10000.0,
            status="active",
        )
        assert valid_customer.credit_limit == 10000.0

        # Invalid credit limit (negative)
        with pytest.raises(ValueError):
            CustomerCreate(
                customer_code="CREDIT002",
                name="Invalid Credit Customer",
                credit_limit=-1000.0,
                status="active",
            )

    def test_customer_field_length_validation(self):
        """Test customer field length validation"""
        # Test customer_code max length
        with pytest.raises(ValueError):
            CustomerCreate(
                customer_code="A" * 51,  # Max is 50
                name="Test Customer",
                status="active",
            )

        # Test name max length
        with pytest.raises(ValueError):
            CustomerCreate(
                customer_code="LONG001",
                name="A" * 256,  # Max is 255
                status="active",
            )


class TestCustomerAPIStructure:
    """Test customer API structure and imports"""

    def test_customer_api_import(self):
        """Test that customer API can be imported successfully"""
        from app.api.v1.customers import router

        assert router is not None

    def test_customer_api_routes_exist(self):
        """Test that customer API routes are properly defined"""
        from app.api.v1.customers import router

        # Check that routes are defined
        routes = [route.path for route in router.routes]
        assert "/" in routes  # List/Create customers
        assert "/{customer_id}" in routes  # Get/Update/Delete customer

    def test_customer_api_methods(self):
        """Test that customer API has correct HTTP methods"""
        from app.api.v1.customers import router

        # Get all route methods
        all_methods = []
        for route in router.routes:
            if hasattr(route, "methods"):
                all_methods.extend(route.methods)

        # Check that CRUD methods are available
        assert "GET" in all_methods
        assert "POST" in all_methods
        assert "PUT" in all_methods
        assert "DELETE" in all_methods

    def test_customer_api_dependencies(self):
        """Test that customer API has proper dependencies"""
        from app.api.v1.customers import router

        # Check that routes have dependencies (authentication)
        for route in router.routes:
            if hasattr(route, "dependant") and route.dependant:
                # Should have dependencies for authentication
                assert len(route.dependant.dependencies) > 0


class TestCustomerAPIIntegration:
    """Test customer API integration without database dependencies"""

    def test_customer_api_in_main_router(self):
        """Test that customer API is included in main router"""
        from app.api.v1.api import api_router

        # Check that customer routes are included
        customer_routes_found = False
        for route in api_router.routes:
            if hasattr(route, "path_regex") and "customers" in str(
                route.path_regex
            ):
                customer_routes_found = True
                break

        assert customer_routes_found, (
            "Customer routes not found in main API router"
        )

    def test_customer_schemas_integration(self):
        """Test that customer schemas work with API"""
        from app.schemas.customer import CustomerCreate, CustomerResponse

        # Test that schemas can be used for API serialization
        customer_data = {
            "customer_code": "TEST001",
            "name": "Test Customer",
            "status": "active",
        }

        # Should be able to create and validate
        customer_create = CustomerCreate(**customer_data)
        assert customer_create.customer_code == "TEST001"

    def test_customer_model_integration(self):
        """Test that customer model can be imported and used"""
        from app.models.customer import Customer

        # Should be able to access model attributes
        assert hasattr(Customer, "customer_code")
        assert hasattr(Customer, "name")
        assert hasattr(Customer, "organization_id")
        assert hasattr(Customer, "status")
