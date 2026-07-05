# This document describes the class// objects to be used for the **PawPal** application 

**PawPal** is a pet-care planning app design to help users with specialized day to day care for their pets. 

The Core actions of teh app are as follows:
- Add pet
- Add pet meal 
- Schedule Meds 
- Schedule a walk
- Scedule a grooming appointment
- Create a weekly shopping cart for each pet 

With all this information the app should be able to create a daily plan for each pet that is in the system and give reasoning as to why it created that plan in particular. 

**PLANNING CLASSES AND OBJECTS**

class Pet:
    attributes -
    str petname 
    str animaltype 
    str petbreed 
    float age 
    int petid
    dictionary(the key will be the food name, and value will be a list of teh days on which it is eaten) diet
    methods() -
    addpet(petname, animaltype, petbreed, age, petId)
    removepet(petname, petId)
    creatediet(petName, petId, diet)
    addmeds(petName, petId)
    schedulewalk(petName, petId)
    createshoppinglist(petName, petId)

class Owner:
    attributes - 
    str name
    all email
    int phonenumber 
    all password
    methods() - 
    signin
    signout
    signup
    setpassword
    displaypets

