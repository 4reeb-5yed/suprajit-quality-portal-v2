# Architecture & Decision Records (ADR)

In enterprise software engineering, an Architecture Decision Record (ADR) captures the core technological choices and the exact reasoning behind why they were chosen over alternatives. 

This document explains the "Why" behind the Suprajit Quality Portal (V2).

---

## 1. The Deployment Environment (The Constraint)
**The Problem:** The software must run on a physical factory Windows PC, ingest 10,000+ files daily from local network folders, and simultaneously serve a fast, secure web portal to clients on the internet. 
**The Constraint:** It must require **zero IT maintenance**. Factory IT teams cannot be expected to manage complex cloud infrastructure, container orchestration, or database migrations.

---

## 2. The Database: SQLite WAL vs PostgreSQL
**The Alternative (PostgreSQL/MySQL):** Traditional web apps use PostgreSQL. However, PostgreSQL requires a dedicated background service, complex installation, user privilege management, and heavy IT overhead.
**The Choice (SQLite with WAL):** We chose a standalone SQLite database, strictly configured in **Write-Ahead Logging (WAL)** mode.
* **Why:** SQLite requires zero configuration and lives in a single `portal.db` file (making backups as simple as copy-pasting the file). By enabling WAL mode, we unlocked Enterprise-level concurrency. A background thread can ingest 10,000 files while internet users simultaneously search the database, with mathematically zero deadlocks or race conditions.

---

## 3. The Ingestion Engine: N-1 Batching vs Real-Time Watchdog
**The Alternative (Real-Time Watchdog):** V1 attempted to ingest files the exact millisecond they were created in the factory folder. This resulted in catastrophic OS File Lock crashes if a machine was slowly copying a file over the network, or if an engineer still had the Excel file open.
**The Choice (N-1 Lifecycle):** We implemented a nightly background chronological batch processor that strictly processes files from *yesterday* (N-1).
* **Why:** By waiting until the next day, the software mathematically guarantees that the file is completely closed, unlocked, and safe to hash. Furthermore, we injected an `ensure_file_safe()` heuristic that actively tests for Windows OS locks and active network copies before ingestion.

---

## 4. The Runtime: PyInstaller Executable vs Docker Containers
**The Alternative (Docker):** Silicon Valley standardizes on Docker containers. However, deploying Docker on a Windows Factory Server requires WSL2 (Windows Subsystem for Linux), Hyper-V virtualization, and advanced IT knowledge.
**The Choice (PyInstaller + NSSM):** We bundled the entire Python environment, the Flask server, and the database engine into a single compiled `.exe` using PyInstaller, managed by NSSM (Non-Sucking Service Manager).
* **Why:** It allows "Double-Click Deployment." The factory IT team does not even need to install Python. The NSSM wrapper acts as a watchdog, automatically restarting the `.exe` if the server reboots or crashes.

---

## 5. The Frontend: HTMX vs React/Angular
**The Alternative (React SPA):** Building a React frontend requires a complex Node.js build pipeline, massive `node_modules` folders, and API serialization logic.
**The Choice (HTMX + Tailwind CSS):** We utilized HTMX directly inside server-side Jinja templates.
* **Why:** HTMX provides the exact same frictionless, instant "Single Page Application" feel (e.g., searching for a serial number updates the table without reloading the page), but requires zero JavaScript build pipelines. It keeps the binary extremely small and lightning-fast.
