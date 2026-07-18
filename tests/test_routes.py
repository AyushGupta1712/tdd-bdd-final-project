"""
Test Cases for Product Routes
"""
import os
import logging
import unittest
from decimal import Decimal
from urllib.parse import quote_plus
from service import app
from service.models import db, Product
from service.common import status
from tests.factories import ProductFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)
BASE_URL = "/products"


# pylint: disable=too-many-public-methods
class TestProductRoutes(unittest.TestCase):
    """Test Cases for Product Routes"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Product.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests"""
        db.session.close()

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()
        db.session.query(Product).delete()
        db.session.commit()

    def tearDown(self):
        db.session.remove()

    # ----------------------------------------------------------
    # HELPER METHODS
    # ----------------------------------------------------------
    def _create_products(self, count):
        """Factory method to create products in bulk"""
        products = []
        for _ in range(count):
            test_product = ProductFactory()
            response = self.client.post(BASE_URL, json=test_product.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test product",
            )
            new_product = response.get_json()
            test_product.id = new_product["id"]
            products.append(test_product)
        return products

    # ----------------------------------------------------------
    # TEST ERROR HANDLERS
    # ----------------------------------------------------------
    def test_bad_request(self):
        """It should return 400 for bad request"""
        response = self.client.post(BASE_URL, json={"wrong": "data"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_method_not_allowed(self):
        """It should return 405 Method Not Allowed"""
        response = self.client.delete(BASE_URL)
        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def get_product_count(self):
        """Save the current number of products"""
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        return len(data)

    # ----------------------------------------------------------
    # TEST INDEX
    # ----------------------------------------------------------
    def test_index(self):
        """It should return the index page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(b"Product Catalog Administration", response.data)

    # ----------------------------------------------------------
    # TEST CREATE (already provided — do not change)
    # ----------------------------------------------------------
    def test_create_product(self):
        """It should Create a new Product"""
        test_product = ProductFactory()
        logging.debug("Test Product: %s", test_product.serialize())
        response = self.client.post(BASE_URL, json=test_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)
        new_product = response.get_json()
        self.assertEqual(new_product["name"], test_product.name)
        self.assertEqual(new_product["description"], test_product.description)
        self.assertEqual(Decimal(new_product["price"]), test_product.price)
        self.assertEqual(new_product["available"], test_product.available)
        self.assertEqual(new_product["category"], test_product.category.name)

    def test_create_product_with_no_name(self):
        """It should not Create a Product without a name"""
        product = self._create_products(1)[0]
        new_product = product.serialize()
        del new_product["name"]
        response = self.client.post(BASE_URL, json=new_product)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_product_no_content_type(self):
        """It should not Create a Product with no Content-Type"""
        response = self.client.post(BASE_URL, data="bad data")
        self.assertEqual(
            response.status_code,
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
        )

    def test_create_product_wrong_content_type(self):
        """It should not Create a Product with wrong Content-Type"""
        response = self.client.post(
            BASE_URL,
            data={},
            content_type="plain/text"
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
        )

    # ----------------------------------------------------------
    # TEST READ
    # ----------------------------------------------------------
    def test_get_product(self):
        """It should Get a single Product"""
        # Create 1 product and get it from the list
        test_product = self._create_products(1)[0]
        # Make GET request to retrieve the product by its id
        response = self.client.get(f"{BASE_URL}/{test_product.id}")
        # Assert the response status code is 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Get the returned json data
        data = response.get_json()
        # Assert the returned data matches what was sent
        self.assertEqual(data["name"], test_product.name)

    def test_get_product_not_found(self):
        """It should not Get a Product thats not found"""
        # Send GET request with invalid product id of 0
        response = self.client.get(f"{BASE_URL}/0")
        # Assert the response is 404 NOT FOUND
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ----------------------------------------------------------
    # TEST UPDATE
    # ----------------------------------------------------------
    def test_update_product(self):
        """It should Update an existing Product"""
        # Create a product to update
        test_product = ProductFactory()
        response = self.client.post(BASE_URL, json=test_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Update the product description
        new_product = response.get_json()
        new_product["description"] = "unknown"
        response = self.client.put(
            f"{BASE_URL}/{new_product['id']}",
            json=new_product
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        updated_product = response.get_json()
        self.assertEqual(updated_product["description"], "unknown")

    def test_update_product_not_found(self):
        """It should not Update a Product that does not exist"""
        product = ProductFactory()
        response = self.client.put(
            f"{BASE_URL}/0",
            json=product.serialize()
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ----------------------------------------------------------
    # TEST DELETE
    # ----------------------------------------------------------
    def test_delete_product(self):
        """It should Delete a Product"""
        # Create 5 products
        products = self._create_products(5)
        product_count = self.get_product_count()
        test_product = products[0]
        # Make DELETE request
        response = self.client.delete(f"{BASE_URL}/{test_product.id}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(response.data), 0)
        # Assert the product is gone
        response = self.client.get(f"{BASE_URL}/{test_product.id}")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        # Assert total count decreased by 1
        new_count = self.get_product_count()
        self.assertEqual(new_count, product_count - 1)

    # ----------------------------------------------------------
    # TEST LIST ALL
    # ----------------------------------------------------------
    def test_get_product_list(self):
        """It should Get a list of Products"""
        self._create_products(5)
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), 5)

    # ----------------------------------------------------------
    # TEST LIST BY NAME
    # ----------------------------------------------------------
    def test_query_by_name(self):
        """It should Query Products by name"""
        products = self._create_products(5)
        test_name = products[0].name
        name_count = len(
            [product for product in products if product.name == test_name]
        )
        response = self.client.get(
            BASE_URL, query_string=f"name={quote_plus(test_name)}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), name_count)
        for product in data:
            self.assertEqual(product["name"], test_name)

    # ----------------------------------------------------------
    # TEST LIST BY CATEGORY
    # ----------------------------------------------------------
    def test_query_by_category(self):
        """It should Query Products by category"""
        products = self._create_products(10)
        category = products[0].category
        found = [
            product for product in products if product.category == category
        ]
        found_count = len(found)
        logging.debug("Found Products [%d] %s", found_count, found)
        response = self.client.get(
            BASE_URL, query_string=f"category={category.name}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), found_count)
        for product in data:
            self.assertEqual(product["category"], category.name)

    # ----------------------------------------------------------
    # TEST LIST BY AVAILABILITY
    # ----------------------------------------------------------
    def test_query_by_availability(self):
        """It should Query Products by availability"""
        products = self._create_products(10)
        available_products = [
            product for product in products if product.available is True
        ]
        available_count = len(available_products)
        response = self.client.get(
            BASE_URL, query_string="available=true"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), available_count)
        for product in data:
            self.assertEqual(product["available"], True)
