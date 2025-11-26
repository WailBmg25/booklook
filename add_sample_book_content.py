#!/usr/bin/env python
"""Script to add sample content pages to existing books."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from database import SessionLocal
from models.book_model import Book
from models.book_page_model import BookPage


# Sample content for different books
SAMPLE_CONTENTS = {
    "The Great Adventure": [
        """Chapter 1: The Beginning

The adventure began on a cold winter morning when John discovered an ancient map in his grandfather's attic. The map showed a mysterious island that wasn't on any modern charts. The parchment was yellowed with age, and the ink had faded in places, but the island's location was clear.

John had always been fascinated by his grandfather's stories of exploration and discovery. Now, holding this map, he felt a connection to those tales that he had never experienced before. The island was marked with a red X, and beside it, in his grandfather's handwriting, were the words: "The greatest treasure lies not in gold, but in the journey itself."

He knew what he had to do. This wasn't just about finding treasure; it was about honoring his grandfather's legacy and embarking on his own adventure.""",
        
        """Chapter 2: Preparation

John spent the next few weeks preparing for his journey. He studied navigation, learned about sailing, and gathered supplies. His friends thought he was crazy, but John was determined. He sold his car, quit his job, and bought a small sailboat that he named "Legacy" after his grandfather.

The boat wasn't much to look at, but it was seaworthy and had everything he needed for a long voyage. He stocked it with food, water, navigation equipment, and emergency supplies. He also brought his grandfather's journal, hoping it would provide clues about the island.

As the departure date approached, John felt a mix of excitement and nervousness. He was leaving behind everything familiar to chase a dream. But deep down, he knew this was what he was meant to do.""",
        
        """Chapter 3: Setting Sail

The morning of departure was clear and calm. John stood on the dock, looking at his boat and then at the horizon. This was it—the moment he had been preparing for. He untied the mooring lines, started the engine, and slowly motored out of the harbor.

Once he was clear of the breakwater, he raised the sails. The wind filled them, and the boat heeled slightly as it picked up speed. John felt a surge of exhilaration. He was really doing this. He was on his way to find the mysterious island.

The first few days at sea were challenging. John had to adjust to the constant motion, the solitude, and the responsibility of managing everything himself. But gradually, he found his rhythm. He learned to read the wind and waves, to navigate by the stars, and to appreciate the simple beauty of the ocean."""
    ],
    
    "Python Programming Guide": [
        """Chapter 1: Introduction to Python

Python is a high-level, interpreted programming language known for its simplicity and readability. Created by Guido van Rossum and first released in 1991, Python has become one of the most popular programming languages in the world.

What makes Python special? First, its syntax is clean and easy to understand, making it an excellent choice for beginners. Second, it's incredibly versatile—you can use Python for web development, data science, artificial intelligence, automation, and much more.

Python follows the philosophy of "There should be one—and preferably only one—obvious way to do it." This principle, part of the Zen of Python, encourages writing code that is clear and straightforward. Let's start with a simple example:

print("Hello, World!")

This single line of code demonstrates Python's simplicity. In many other languages, you would need multiple lines just to display text on the screen.""",
        
        """Chapter 2: Variables and Data Types

In Python, variables are containers for storing data values. Unlike some other programming languages, Python has no command for declaring a variable. A variable is created the moment you first assign a value to it.

Python has several built-in data types:
- Integers (int): Whole numbers like 5, -3, 1000
- Floats (float): Decimal numbers like 3.14, -0.5, 2.0
- Strings (str): Text enclosed in quotes like "Hello" or 'Python'
- Booleans (bool): True or False values
- Lists: Ordered collections like [1, 2, 3]
- Dictionaries: Key-value pairs like {"name": "John", "age": 30}

Here are some examples:

name = "Alice"
age = 25
height = 5.6
is_student = True
grades = [85, 90, 78, 92]

Python is dynamically typed, meaning you don't need to specify the type of a variable when you create it. Python figures it out automatically.""",
        
        """Chapter 3: Control Flow

Control flow statements allow you to control the execution of your code based on conditions. The most common control flow statements in Python are if, elif, else, for, and while.

The if statement allows you to execute code only if a certain condition is true:

age = 18
if age >= 18:
    print("You are an adult")
else:
    print("You are a minor")

The for loop allows you to iterate over a sequence:

fruits = ["apple", "banana", "cherry"]
for fruit in fruits:
    print(fruit)

The while loop repeats code as long as a condition is true:

count = 0
while count < 5:
    print(count)
    count += 1

Understanding control flow is essential for writing programs that can make decisions and repeat actions."""
    ],
    
    "Space Odyssey": [
        """Prologue: The Signal

In the year 2157, humanity had spread across the solar system. Mars was colonized, mining operations thrived in the asteroid belt, and research stations orbited Jupiter's moons. But despite all this progress, we had never encountered any sign of extraterrestrial intelligence.

That changed on a Tuesday morning when the deep space listening array detected something unusual. It wasn't random cosmic noise or a natural phenomenon. It was a signal—a pattern that repeated every 47 seconds. The signal came from beyond our solar system, from a star system 12 light-years away.

Dr. Sarah Chen was the first to analyze the signal. As she studied the data, her hands trembled. This wasn't just a signal; it was a message. Someone—or something—was trying to communicate with us. The question was: what were they trying to say?""",
        
        """Chapter 1: The Mission

Within weeks, the United Earth Space Agency had assembled a team for an unprecedented mission. They would travel to the source of the signal using the newly developed quantum drive, which could achieve speeds approaching light speed. The journey would take five years each way.

Captain Marcus Rodriguez was chosen to lead the mission. A veteran of three Mars expeditions, he was known for his calm demeanor and quick thinking. His crew included Dr. Chen, the linguist who had decoded parts of the message; Dr. James Park, an astrophysicist; and Lieutenant Maya Okonkwo, the ship's pilot and engineer.

Their ship, the Odyssey, was the most advanced vessel ever built. It carried enough supplies for a twelve-year journey, advanced scientific equipment, and a powerful AI named ARIA to assist with navigation and analysis. As they prepared for launch, the world watched with a mixture of excitement and apprehension.""",
        
        """Chapter 2: Into the Unknown

The launch was flawless. As the Odyssey left Earth's orbit and engaged its quantum drive, the crew felt the strange sensation of space-time warping around them. Stars stretched into lines of light, and then everything stabilized. They were traveling faster than any humans had ever traveled before.

The first months of the journey were spent in routine. The crew conducted experiments, maintained the ship, and continued analyzing the signal. Dr. Chen made progress in understanding the message's structure, though its meaning remained elusive. It seemed to be a greeting, an invitation, or perhaps a warning.

As they crossed the heliopause and left the solar system behind, Captain Rodriguez gathered the crew. "We're truly in uncharted territory now," he said. "Whatever we find out there, we face it together." The crew nodded, each lost in their own thoughts about what awaited them at journey's end."""
    ]
}


def add_content_to_books():
    """Add sample content pages to existing books."""
    db = SessionLocal()
    
    try:
        # Get all books
        books = db.query(Book).all()
        
        if not books:
            print("No books found in database. Please run add_sample_data.py first.")
            return
        
        print(f"Found {len(books)} books in database")
        
        for book in books:
            # Check if book already has content
            existing_pages = db.query(BookPage).filter(BookPage.book_id == book.id).count()
            if existing_pages > 0:
                print(f"  ⏭️  Skipping '{book.titre}' (already has {existing_pages} pages)")
                continue
            
            # Find matching content
            content_pages = SAMPLE_CONTENTS.get(book.titre, [])
            
            if not content_pages:
                print(f"  ⚠️  No sample content available for '{book.titre}'")
                continue
            
            print(f"  📖 Adding {len(content_pages)} pages to '{book.titre}'...")
            
            # Create pages
            for page_num, content in enumerate(content_pages, start=1):
                page = BookPage(
                    book_id=book.id,
                    page_number=page_num,
                    content=content
                )
                page.calculate_word_count()
                db.add(page)
            
            db.commit()
            
            # Update book statistics
            total_pages = len(content_pages)
            total_words = sum(len(content.split()) for content in content_pages)
            
            book.total_pages = total_pages
            book.word_count = total_words
            db.commit()
            
            print(f"     ✅ Added {total_pages} pages ({total_words} words)")
        
        print("\n" + "="*60)
        print("✅ Sample content added successfully!")
        print("="*60)
        
        # Print summary
        total_books_with_content = db.query(Book).filter(Book.total_pages > 0).count()
        total_pages = db.query(BookPage).count()
        
        print(f"\nSummary:")
        print(f"  Books with content: {total_books_with_content}")
        print(f"  Total pages: {total_pages}")
        
    except Exception as e:
        print(f"❌ Error adding content: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    add_content_to_books()
