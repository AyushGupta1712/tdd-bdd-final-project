"""
Test Cases for Product Model
"""
import os
import logging
import unittest
from service.models import Product, Category, db, DataValidationError
from service import app
from tests.factories import ProductFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

logger = logging.getLogger("flask.app")


class TestProductModel(unittest.TestCase):
    """Test Cases for Product Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Product.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Product).delete()
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    # ---------------------------------------------------------------
    # TEST CASES (already provided — DO NOT change these)
    # ---------------------------------------------------------------
    def test_create_a_product(self):
        """It should Create a product and assert that it exists"""
        product = Product(
            name="Fedora",
            description="A red hat",
            price=12.50,
            available=True,
            category=Category.CLOTHS,
        )
        self.assertEqual(str(product), "<Product Fedora id=[None]>")
        self.assertTrue(product is not None)
        self.assertEqual(product.id, None)
        self.assertEqual(product.name, "Fedora")
        self.assertEqual(product.price, 12.50)
        self.assertEqual(product.available, True)
        self.assertEqual(product.category, Category.CLOTHS)

    def test_add_a_product(self):
        """It should Create a product and add it to the database"""
        products = Product.all()
        self.assertEqual(products, [])
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        products = Product.all()
        self.assertEqual(len(products), 1)

    # ---------------------------------------------------------------
    # EXERCISE 2 — YOUR TEST CASES START HERE
    # ---------------------------------------------------------------

    def test_read_a_product(self):
        """It should Read a Product"""
        product = ProductFactory()
        logger.info("Product: %s", product)
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        # Fetch the product back from the database using its ID
        found_product = Product.find(product.id)
        # Assert the properties match the original product
        self.assertEqual(found_product.id, product.id)
        self.assertEqual(found_product.name, product.name)
        self.assertEqual(found_product.description, product.description)
        self.assertEqual(found_product.price, product.price)

    def test_update_a_product(self):
        """It should Update a Product"""
        product = ProductFactory()
        logger.info("Product: %s", product)
        product.id = None
        product.create()
        logger.info("Product after create: %s", product)
        self.assertIsNotNone(product.id)
        # Update the description
        product.description = "testing"
        original_id = product.id
        product.update()
        # Assert the id is the same but description is updated
        self.assertEqual(product.id, original_id)
        self.assertEqual(product.description, "testing")
        # Fetch all products and verify only one exists
        products = Product.all()
        self.assertEqual(len(products), 1)
        # Assert the fetched product has the original id and updated description
        self.assertEqual(products[0].id, original_id)
        self.assertEqual(products[0].description, "testing")

    def test_delete_a_product(self):
        """It should Delete a Product"""
        product = ProductFactory()
        product.create()
        # Assert there is only one product in the database
        self.assertEqual(len(Product.all()), 1)
        # Delete the product
        product.delete()
        # Assert the product has been deleted
        self.assertEqual(len(Product.all()), 0)

    def test_list_all_products(self):
        """It should List all Products in the database"""
        products = Product.all()
        # Assert there are no products at the start
        self.assertEqual(products, [])
        # Create 5 products and save them to the database
        for _ in range(5):
            product = ProductFactory()
            product.create()
        # Fetch all products again
        products = Product.all()
        # Assert there are now 5 products
        self.assertEqual(len(products), 5)

    def test_find_by_name(self):
        """It should Find a Product by Name"""
        products = ProductFactory.create_batch(5)
        # Save all products to the database
        for product in products:
            product.create()
        # Get the name of the first product
        name = products[0].name
        # Count how many products have that name
        count = len([p for p in products if p.name == name])
        # Find products by name from the database
        found = Product.find_by_name(name)
        # Assert the count matches
        self.assertEqual(found.count(), count)
        # Assert each found product has the correct name
        for product in found:
            self.assertEqual(product.name, name)

    def test_find_by_availability(self):
        """It should Find Products by Availability"""
        products = ProductFactory.create_batch(10)
        # Save all products to the database
        for product in products:
            product.create()
        # Get the availability of the first product
        available = products[0].available
        # Count how many products have that availability
        count = len([p for p in products if p.available == available])
        # Find products by availability from the database
        found = Product.find_by_availability(available)
        # Assert the count matches
        self.assertEqual(found.count(), count)
        # Assert each found product has the correct availability
        for product in found:
            self.assertEqual(product.available, available)

    def test_find_by_category(self):
        """It should Find Products by Category"""
        products = ProductFactory.create_batch(10)
        # Save all products to the database
        for product in products:
            product.create()
        # Get the category of the first product
        category = products[0].category
        # Count how many products have that category
        count = len([p for p in products if p.category == category])
        # Find products by category from the database
        found = Product.find_by_category(category)
        # Assert the count matches
        self.assertEqual(found.count(), count)
        # Assert each found product has the correct category
        for product in found:
            self.assertEqual(product.category, category)

    def test_update_product_with_no_id(self):
        """It should not Update a Product with no id"""
        product = ProductFactory()
        product.id = None
        self.assertRaises(DataValidationError, product.update)

    def test_find_by_price(self):
        """It should Find Products by Price"""
        products = ProductFactory.create_batch(10)
        for product in products:
            product.create()
        price = products[0].price
        count = len([p for p in products if p.price == price])
        found = Product.find_by_price(price)
        self.assertEqual(found.count(), count)
        for product in found:
            self.assertEqual(product.price, price)

    def test_deserialize_with_no_data(self):
        """It should not deserialize a Product with no data"""
        product = Product()
        self.assertRaises(DataValidationError, product.deserialize, None)

    def test_deserialize_bad_available(self):
        """It should not deserialize a bad available attribute"""
        data = {
            "id": 1,
            "name": "Fedora",
            "description": "A red hat",
            "price": "2.00",
            "available": "yes",
            "category": "CLOTHS",
        }
        product = Product()
        self.assertRaises(DataValidationError, product.deserialize, data)
