# Administrator & Troubleshooting Guide

This guide details the logical workflows for managing clients, handling data ingestion, and troubleshooting the system.

## Client Management Flow
The portal utilizes a **Tabular CRUD** architecture to ensure clean database relationships. To onboard a new client (e.g., TVS):
1. **Customers Tab:** Click "Add Customer". Create the profile for TVS.
2. **Recipes Tab:** Click "Add Recipe". Assign specific factory recipe names to TVS.
3. **Users Tab:** Click "Add User". Create the login credentials for the TVS engineer and assign them to the TVS customer profile. 

*(Note: The system automatically enforces an 8-character, 1-number, 1-symbol Password Complexity rule when creating users).*

## The Ingestion Engine
The background ingestion engine uses an **N-1 Day Lifecycle**.
* **What this means:** When the engine runs today, it only scans files modified *yesterday or earlier*. 
* **Why:** This mathematically guarantees that no file is currently locked by a factory machine or halfway through a network copy, preventing database crashes.

## The Repair Dashboard
If corrupted data enters the system or a manual override is required, do not edit the SQLite database directly. Use the Repair Dashboard:

* **Dry Run (Trace Simulator):** Click this to safely scan the factory folder without writing to the database. It outputs a detailed log of exactly what *would* happen (what would parse, fail, or insert).
* **Purge Date:** If a specific day's batch was completely corrupted, type the date and click Purge. It surgically deletes that day's reports from the UI.
* **Force Sync:** Manually overrides the automated daily timer and triggers an immediate background sync.
