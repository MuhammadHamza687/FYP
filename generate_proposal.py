"""
FYP Proposal Generator - Multi-Channel Inventory and Order Synchronization System
Run: python generate_proposal.py
Output: FYP_Proposal_Final.docx
"""

from docx import Document
from docx.shared import Pt, Inches, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import copy

doc = Document()

# ─────────────────────────────────────────────
# PAGE SETUP  –  A4, margins as per guidelines
# ─────────────────────────────────────────────
section = doc.sections[0]
section.page_width  = Cm(21.0)
section.page_height = Cm(29.7)
section.top_margin    = Cm(2.54)
section.bottom_margin = Cm(2.54)
section.left_margin   = Cm(2.54)
section.right_margin  = Cm(2.54)

# ─────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────
FONT = "Times New Roman"

def set_para_format(para, space_before=0, space_after=6, line_spacing=None):
    fmt = para.paragraph_format
    fmt.space_before = Pt(space_before)
    fmt.space_after  = Pt(space_after)
    fmt.alignment    = WD_ALIGN_PARAGRAPH.JUSTIFY
    if line_spacing:
        from docx.shared import Pt as pt
        fmt.line_spacing = pt(line_spacing)

def add_heading1(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after  = Pt(6)
    run = p.add_run(text)
    run.font.name = FONT
    run.font.size = Pt(16)
    run.font.bold = True
    return p

def add_heading2(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after  = Pt(4)
    run = p.add_run(text)
    run.font.name = FONT
    run.font.size = Pt(14)
    run.font.bold = True
    return p

def add_body(doc, text, bold=False, italic=False, space_after=6):
    p = doc.add_paragraph()
    set_para_format(p, space_after=space_after)
    run = p.add_run(text)
    run.font.name = FONT
    run.font.size = Pt(11)
    run.font.bold   = bold
    run.font.italic = italic
    return p

def add_bullet(doc, text, level=0):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after  = Pt(3)
    run = p.add_run(text)
    run.font.name = FONT
    run.font.size = Pt(11)
    return p

def set_cell_text(cell, text, bold=False, size=11, align=WD_ALIGN_PARAGRAPH.LEFT):
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = align
    run = p.add_run(text)
    run.font.name = FONT
    run.font.size = Pt(size)
    run.font.bold = bold

def shade_cell(cell, hex_color="D9D9D9"):
    tc   = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd  = OxmlElement("w:shd")
    shd.set(qn("w:val"),   "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"),  hex_color)
    tcPr.append(shd)

# ══════════════════════════════════════════════
# COVER PAGE
# ══════════════════════════════════════════════
def cover_center(text, size=14, bold=False, space_after=6):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after  = Pt(space_after)
    run = p.add_run(text)
    run.font.name = FONT
    run.font.size = Pt(size)
    run.font.bold = bold
    return p

cover_center("Multi-Channel Inventory and Order Synchronization System", 16, True, 10)
cover_center("Final Year Project Proposal", 14, True, 6)
cover_center("Session 2023–2027", 12, False, 20)
cover_center("A project submitted in partial fulfillment of the requirements for the Degree of", 11, False, 4)
cover_center("BS in Software Engineering", 13, True, 20)
cover_center("Department of Computer Science", 12, True, 4)
cover_center("COMSATS University Islamabad (CUI), Lahore Campus", 12, False, 0)

doc.add_page_break()

# ══════════════════════════════════════════════
# PROJECT REGISTRATION TABLE
# ══════════════════════════════════════════════
add_heading1(doc, "Project Registration")

reg_table = doc.add_table(rows=3, cols=2)
reg_table.style = "Table Grid"
reg_data = [
    ("Project ID (for office use)", ""),
    ("Type of project", "[✓] Traditional  [ ] Industrial  [ ] Continuing"),
    ("Nature of project", "[✓] Development  [ ] Research & Development"),
]
for i, (label, val) in enumerate(reg_data):
    set_cell_text(reg_table.rows[i].cells[0], label, bold=True)
    set_cell_text(reg_table.rows[i].cells[1], val)

# SDGs
sdg_table = doc.add_table(rows=1, cols=2)
sdg_table.style = "Table Grid"
set_cell_text(sdg_table.rows[0].cells[0], "Sustainable Development Goals (SDGs)", bold=True)
set_cell_text(sdg_table.rows[0].cells[1],
    "[ ] Good Health and Well-Being\n"
    "[ ] Quality Education\n"
    "[✓] Industry, Innovation, and Infrastructure\n"
    "[ ] Gender Equality\n"
    "[✓] Decent Work and Economic Growth\n"
    "[ ] Climate Action")

# Area
area_table = doc.add_table(rows=1, cols=2)
area_table.style = "Table Grid"
set_cell_text(area_table.rows[0].cells[0], "Area of specialization", bold=True)
set_cell_text(area_table.rows[0].cells[1],
    "[ ] Artificial Intelligence (AI)   [ ] Blockchain   [ ] Cybersecurity\n"
    "[ ] Data Science and Analytics     [ ] Game Development\n"
    "[ ] Internet of Things (IoT)       [ ] Natural Language Processing\n"
    "[ ] Mobile App Development         [✓] Web Development")

doc.add_paragraph()

# ── Group Members ──
add_heading2(doc, "Project Group Members")
mem_table = doc.add_table(rows=4, cols=6)
mem_table.style = "Table Grid"
mem_table.alignment = WD_TABLE_ALIGNMENT.CENTER
headers = ["Sr.#", "Reg. #", "Student Name", "Email ID", "Phone #", "Signature"]
for j, h in enumerate(headers):
    set_cell_text(mem_table.rows[0].cells[j], h, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
    shade_cell(mem_table.rows[0].cells[j])

members = [
    ("(i) Group Leader", "FA23-BSE-111", "Muhammad Hamza", "fa23-bse-111@cuilahore.edu.pk", "", ""),
    ("(ii)",             "FA23-BSE-041", "Asadullah Naeem","fa23-bse-041@cuilahore.edu.pk", "", ""),
    ("(iii)",            "FA23-BSE-132", "Muhammad Sami",  "fa23-bse-132@cuilahore.edu.pk", "", ""),
]
for i, row_data in enumerate(members):
    for j, val in enumerate(row_data):
        set_cell_text(mem_table.rows[i+1].cells[j], val)

doc.add_paragraph()

# ── Declaration ──
p = doc.add_paragraph()
set_para_format(p)
run = p.add_run(
    "Declaration: FYP group members have cleared all prerequisite courses for FYP-I as per their "
    "degree requirements. For BS (Software Engineering): CSC241 Object Oriented Programming, "
    "CSC291 Software Engineering Concepts, CSC270 Database Systems, HUM102 Report Writing Skills."
)
run.font.name = FONT; run.font.size = Pt(11); run.font.italic = True

doc.add_paragraph()

# ── Plagiarism Free Certificate ──
add_heading2(doc, "Plagiarism Free Certificate")
add_body(doc,
    "This is to certify that, I am ________________________ S/D/o _______________________, "
    "group leader of FYP under registration no CUI / FA23-BSE-111 /LHR at the Computer Science Department, "
    "COMSATS Institute of Information Technology, Lahore. I declare that my FYP proposal is checked by my "
    "supervisor and the similarity index is ________% that is less than 20%, an acceptable limit by HEC. "
    "The report is attached herewith as Appendix A.")

doc.add_paragraph()

sup_table = doc.add_table(rows=3, cols=4)
sup_table.style = "Table Grid"
sup_labels = [
    ("Date:", "", "Name of Group Leader:", ""),
    ("Name of Supervisor:", "", "Co-Supervisor (if any):", ""),
    ("Designation:", "", "Designation:", ""),
]
for i, row_data in enumerate(sup_labels):
    for j, val in enumerate(row_data):
        bold = (j % 2 == 0)
        set_cell_text(sup_table.rows[i].cells[j], val, bold=bold)

doc.add_page_break()

# ══════════════════════════════════════════════
# ABSTRACT
# ══════════════════════════════════════════════
add_heading1(doc, "Abstract")
add_body(doc,
    "The rapid expansion of digital commerce has enabled businesses to sell products simultaneously "
    "across multiple online marketplaces such as Amazon, Shopify, and eBay, increasing global market reach "
    "and revenue potential. Each platform maintains independent inventory databases and API ecosystems, "
    "creating a growing need for automated, cross-platform synchronization mechanisms that can sustain "
    "operational accuracy at scale. Distributed systems research consistently identifies inventory visibility "
    "and real-time data consistency as critical factors for reducing operational inefficiencies in multi-channel "
    "retail environments [1]. As e-commerce order volumes continue to grow, the technical challenges of "
    "maintaining synchronized stock levels across independent platforms have become increasingly complex "
    "and commercially significant. "
    "Despite this need, multi-channel sellers frequently encounter overselling, order cancellations, and "
    "reputational damage caused by delayed or failed inventory updates. Existing commercial synchronization "
    "tools are often prohibitively expensive, lack flexibility for customization, and rely on periodic batch "
    "updates rather than event-driven architectures, increasing the risk of stock inconsistencies. API rate "
    "limits, network latency, concurrency conflicts during simultaneous order placements, and inadequate "
    "failure recovery mechanisms further compound these operational challenges. There is a clear gap in the "
    "availability of cost-effective, academically grounded, and concurrency-safe synchronization systems. "
    "This project proposes the design and development of a centralized Multi-Channel Inventory and Order "
    "Synchronization System built using Python FastAPI, PostgreSQL, Redis, and Celery. The system will "
    "integrate Shopify and Amazon Selling Partner APIs, maintain a master inventory database as the single "
    "source of truth, detect orders in real time through webhook-based event listeners, and process "
    "synchronization jobs through a distributed task queue with atomic transactions and row-level locking "
    "to prevent race conditions. An administrative dashboard will provide real-time monitoring of "
    "synchronization status and error logs. "
    "The expected outcome is a fully functional, scalable, and reliable inventory synchronization platform "
    "capable of preventing overselling under concurrent order conditions. The system will demonstrate "
    "synchronization latency below 30 seconds under normal conditions, handle a minimum of 50 concurrent "
    "orders without database conflicts, and maintain complete synchronization logs traceable for auditing. "
    "The project provides practical exposure to distributed systems engineering, API integration, event-driven "
    "architectures, and concurrency control—competencies directly relevant to modern software engineering practice.")

doc.add_page_break()

# ══════════════════════════════════════════════
# 1. INTRODUCTION
# ══════════════════════════════════════════════
add_heading1(doc, "1.   Introduction")

add_heading2(doc, "1.1   Domain Background")
add_body(doc,
    "The rapid advancement of digital technologies has fundamentally transformed the nature of global "
    "commerce, enabling businesses to transcend physical boundaries and operate across international "
    "online marketplaces. Platforms such as Amazon, Shopify, and eBay have become central infrastructure "
    "for product listing, transaction processing, and customer acquisition at a global scale. Multi-channel "
    "selling, where a seller simultaneously lists identical products across multiple platforms, has become "
    "a widely adopted strategy to maximize market visibility and reduce dependency on any single sales "
    "channel. This model increases revenue opportunities but introduces a proportionally significant set "
    "of technical and operational coordination challenges that must be addressed systematically.")
add_body(doc,
    "Each marketplace operates its own independent database, API structure, inventory management model, "
    "authentication system, and rate-limiting policy. When a product is purchased on one platform, the "
    "stock level must be updated immediately across all other connected platforms to maintain consistency "
    "and prevent customers from ordering unavailable items. Failure to achieve this synchronization in "
    "real time results in sellers facing overselling incidents, forced order cancellations, refund "
    "processing costs, negative seller ratings, and potential account suspension. As transaction volumes "
    "grow, these challenges become exponentially more complex due to concurrent order placements, API "
    "communication delays, network failures, and the risk of race conditions in shared inventory records. "
    "A centralized, automated, and scalable mechanism is therefore essential to maintain operational "
    "integrity across multi-channel e-commerce environments [2].")

add_heading2(doc, "1.2   Motivation and Significance of the Project")
add_body(doc,
    "Inventory inaccuracies are among the primary drivers of order cancellations and customer "
    "dissatisfaction in online retail. Supply chain management research by Chopra and Meindl [1] "
    "demonstrates that effective inventory synchronization significantly reduces operational inefficiencies "
    "and financial losses. Existing commercial synchronization tools address this problem at a practical "
    "level but typically involve high recurring subscription costs, limited API customization, and "
    "inadequate handling of concurrent transactions across platforms. Furthermore, most available tools "
    "rely on periodic polling rather than event-driven architectures, introducing synchronization delays "
    "that increase the probability of overselling. The motivation for this project is to engineer a "
    "technically rigorous, cost-effective, and concurrency-safe solution tailored for multi-channel "
    "sellers, while simultaneously providing the development team with practical exposure to distributed "
    "systems design, real-time API integration, and scalable backend engineering.")

add_heading2(doc, "1.3   Objectives and Scope of the Project")
add_body(doc,
    "The primary objective is to design and develop a centralized inventory synchronization system "
    "integrating two major e-commerce platforms—Shopify and Amazon Selling Partner API—through their "
    "official authentication interfaces. The system scope includes backend development using Python "
    "FastAPI, a PostgreSQL master inventory database, Redis-backed Celery task queues, webhook-based "
    "real-time order detection, atomic transaction processing with row-level locking, and a React.js "
    "administrative dashboard. The project explicitly excludes payment gateway integration, logistics "
    "and shipment tracking, mobile application development, financial accounting modules, customer "
    "notification systems, and multi-currency support. The focus is strictly confined to inventory "
    "quantity management and order-driven synchronization across the two selected platforms.")

add_heading2(doc, "1.4   Proposed Solution")
add_body(doc,
    "The proposed system adopts a centralized, event-driven architecture in which a PostgreSQL master "
    "database serves as the single source of truth for all inventory data. The backend is built using "
    "Python FastAPI for its native asynchronous capabilities, which are well-suited to the I/O-intensive "
    "nature of concurrent multi-platform API communication. When an order is placed on any integrated "
    "platform, a digitally signed webhook notification triggers the synchronization pipeline. The order "
    "event is validated and dispatched to a Celery distributed task queue backed by Redis. A dedicated "
    "worker process acquires a row-level database lock on the relevant product record, performs an "
    "atomic stock deduction within a database transaction, and subsequently dispatches inventory update "
    "API calls to the remaining connected platforms. Failed API calls are handled by an exponential "
    "backoff retry policy with a dead-letter queue for permanently failed tasks.")

add_heading2(doc, "1.5   Expected Results and Outcomes")
add_body(doc,
    "The project is expected to deliver a fully functional inventory synchronization platform that "
    "prevents overselling under real-time concurrent order conditions. The system will achieve "
    "measurable synchronization latency below 30 seconds under standard network conditions and "
    "successfully handle a minimum of 50 simultaneous orders without race conditions or database "
    "conflicts. Comprehensive synchronization logs, performance test reports, API integration evidence, "
    "architecture diagrams, and load testing results will be produced as documentary evidence "
    "of goal achievement. The project contributes a practical, industry-relevant solution to "
    "multi-channel e-commerce management while demonstrating applied competence in distributed "
    "systems, event-driven architectures, and scalable backend engineering.")

# ══════════════════════════════════════════════
# 2. PROBLEM STATEMENT
# ══════════════════════════════════════════════
add_heading1(doc, "2.   Problem Statement")
add_body(doc,
    "Multi-channel e-commerce sellers face critical operational challenges in maintaining synchronized "
    "inventory across independent marketplaces such as Amazon and Shopify, where each platform operates "
    "its own isolated database and API ecosystem. When a product is sold on one platform, stock levels "
    "frequently fail to update instantly on others due to API rate limits, network latency, and the "
    "absence of event-driven synchronization, resulting in overselling, forced order cancellations, "
    "and reputational damage. Concurrent order placements across multiple channels introduce race "
    "conditions in shared inventory records that existing tools fail to handle safely, while "
    "reliance on periodic batch updates rather than real-time webhook-driven architectures further "
    "increases inconsistency risk. Commercial solutions are either prohibitively expensive, "
    "insufficiently customizable, or lack robust concurrency control and failure recovery mechanisms, "
    "creating a clear need for a centralized, cost-effective, and concurrency-safe synchronization "
    "system that ensures real-time accuracy, prevents overselling, and provides transparent "
    "operational monitoring for multi-channel e-commerce businesses.")

# ══════════════════════════════════════════════
# 3. PROJECT OBJECTIVES
# ══════════════════════════════════════════════
add_heading1(doc, "3.   Project Objectives")
objectives = [
    "To analyze and document the API structures, authentication mechanisms, and rate-limit policies of Shopify and Amazon Selling Partner API.",
    "To design a centralized PostgreSQL master inventory database schema serving as a single, authoritative source of truth for all stock data.",
    "To develop a multi-channel inventory and order synchronization backend platform integrating Shopify and Amazon marketplace APIs using Python FastAPI.",
    "To implement real-time order detection using HTTPS webhook-based event listeners with cryptographic signature verification.",
    "To introduce a Celery and Redis-based distributed queue processing approach for managing API rate limits, task scheduling, and retry logic.",
    "To implement concurrency control mechanisms using atomic PostgreSQL transactions and row-level locking to prevent race conditions during simultaneous order placements.",
    "To build a React.js administrative monitoring dashboard for tracking synchronization status, error logs, and system health in real time.",
    "To evaluate system performance through load testing with simultaneous order simulations, measuring synchronization latency, API error rates, and stock consistency.",
]
for obj in objectives:
    add_bullet(doc, obj)

# ══════════════════════════════════════════════
# 4. RELATED WORK
# ══════════════════════════════════════════════
add_heading1(doc, "4.   Related Work")
add_body(doc,
    "Inventory synchronization and distributed data consistency have been studied extensively in both "
    "supply chain management and distributed systems research. Chopra and Meindl [1] establish that "
    "inventory visibility and real-time coordination are foundational to reducing operational "
    "inefficiencies and preventing stock inconsistencies in multi-channel retail. Their work directly "
    "frames the problem this project addresses: poor synchronization mechanisms have measurable "
    "negative impact on customer satisfaction and seller profitability.")
add_body(doc,
    "Tanenbaum and Van Steen [2] provide a comprehensive treatment of distributed systems principles "
    "including consistency models, concurrency control, and fault tolerance. Their discussion of "
    "eventual consistency and atomic operations informs the transaction strategy adopted in this "
    "project. Fowler [3] extends these principles to enterprise application design, introducing "
    "transactional boundary patterns and event-driven architectures that underpin modern scalable "
    "backend systems. The row-level locking and atomic deduction strategy proposed in this project "
    "directly applies Fowler's Unit of Work and optimistic concurrency patterns.")
add_body(doc,
    "Garcia-Molina, Ullman, and Widom [4] provide the theoretical foundation for transaction "
    "isolation levels, deadlock prevention, and serializable operations in relational databases, "
    "which are central to the PostgreSQL concurrency control strategy employed here. Kleppmann [5] "
    "modernizes these concepts in the context of data-intensive applications, specifically addressing "
    "the challenges of distributed transactions, message queues, and idempotent processing—all "
    "directly applicable to this project's queue-based synchronization engine.")
add_body(doc,
    "Amazon's Selling Partner API documentation [6] outlines rate-limiting policies, OAuth 2.0 "
    "authentication flows, and asynchronous feed submission requirements for inventory updates. "
    "Shopify's webhook and Admin API documentation [7] demonstrates event-driven order notification "
    "patterns with HMAC signature verification. eBay's developer API documentation [8] provides "
    "additional context on multi-platform API variation, informing the modular integration layer "
    "design. Fielding's foundational REST dissertation [9] underpins the RESTful API communication "
    "strategy throughout the system. DeCandia et al. [10] in their description of Amazon Dynamo "
    "illustrate key-value store consistency trade-offs and replication strategies that contextualize "
    "the eventual consistency challenges this project manages through atomic transactions and queues.")

# ══════════════════════════════════════════════
# 5. PROPOSED METHODOLOGY AND ARCHITECTURE
# ══════════════════════════════════════════════
add_heading1(doc, "5.   Proposed Methodology and Architecture")

add_heading2(doc, "5.1   Development Methodology")
add_body(doc,
    "The system will be developed using an incremental, phase-based methodology where each component "
    "is independently designed, implemented, unit-tested, and validated before integration. This "
    "approach reduces integration risk and allows early identification of API compatibility issues. "
    "Six structured phases have been defined:")

phases = [
    ("Phase 1 – Requirement Analysis and API Study (September 2026):",
     "Study Shopify Admin API and Amazon SP-API documentation. Identify OAuth 2.0 flows, "
     "rate-limit policies, webhook payload schemas, and inventory update endpoints. Define all "
     "functional and non-functional requirements."),
    ("Phase 2 – System Design (October 2026):",
     "Design the PostgreSQL master inventory database schema. Define data models for products, "
     "platform listings, orders, sync logs, and queue tasks. Finalize concurrency control and "
     "transaction isolation strategy. Produce architecture diagrams."),
    ("Phase 3 – Integration Module Development (November 2026):",
     "Implement OAuth 2.0 authentication for both platforms. Develop platform-specific API service "
     "classes for inventory reads and writes. Implement HTTPS webhook endpoints with HMAC signature "
     "verification. Build error handling and exponential backoff retry policies."),
    ("Phase 4 – Synchronization Engine Implementation (December 2026):",
     "Develop the central Celery-based event processing engine. Implement atomic PostgreSQL "
     "transactions with SELECT FOR UPDATE row-level locking. Configure Redis task queues with "
     "priority lanes and dead-letter queues. Implement rollback and partial-failure compensation logic."),
    ("Phase 5 – Dashboard and Monitoring (January–February 2027):",
     "Develop the React.js administrative interface. Display real-time synchronization logs, "
     "stock levels, API error rates, retry counts, and system health indicators."),
    ("Phase 6 – Testing and Evaluation (March–April 2027):",
     "Perform unit testing using pytest and integration testing across both platforms. Conduct "
     "load testing with Apache JMeter simulating 50+ concurrent orders. Measure synchronization "
     "latency, API error rates, and stock consistency under stress conditions."),
]
for title, detail in phases:
    p = doc.add_paragraph()
    set_para_format(p, space_after=4)
    r1 = p.add_run(title + " ")
    r1.font.name = FONT; r1.font.size = Pt(11); r1.font.bold = True
    r2 = p.add_run(detail)
    r2.font.name = FONT; r2.font.size = Pt(11)

add_heading2(doc, "5.2   System Architecture")
add_body(doc,
    "The proposed system follows a centralized, event-driven architecture consisting of six core "
    "layers, as described below.")

components = [
    ("1. API Integration Layer:", "Manages OAuth 2.0 token acquisition and refresh, platform-specific HTTP request construction, response parsing, rate-limit header monitoring, and per-platform retry budgets."),
    ("2. Webhook / Event Listener Layer:", "HTTPS FastAPI endpoints that receive signed order placement events from Shopify and Amazon. Each event is validated via HMAC/SHA-256 signature verification before being serialized and pushed to the Celery task queue."),
    ("3. Central PostgreSQL Inventory Database:", "Maintains product records, current stock quantities, platform listing mappings (SKU to platform-specific IDs), order history, synchronization logs, and queue task state. Serves as the single source of truth."),
    ("4. Synchronization Engine (Celery Workers):", "Core processing logic. Each worker acquires a row-level lock (SELECT FOR UPDATE) within a serializable transaction, deducts stock atomically, commits, then dispatches inventory update tasks to all other connected platforms. Implements saga-style compensation on partial failures."),
    ("5. Redis Queue Management System:", "Provides task persistence, worker scheduling, priority queuing, rate-limit-aware throttling, exponential backoff retry scheduling, and a dead-letter queue for permanently failed tasks."),
    ("6. React.js Administrative Dashboard:", "Real-time interface displaying synchronization status per order, stock levels, failed sync attempts, retry history, API error rates, and system health metrics via FastAPI WebSocket or polling endpoints."),
]
for title, detail in components:
    p = doc.add_paragraph()
    set_para_format(p, space_after=4)
    r1 = p.add_run(title + " ")
    r1.font.name = FONT; r1.font.size = Pt(11); r1.font.bold = True
    r2 = p.add_run(detail)
    r2.font.name = FONT; r2.font.size = Pt(11)

add_heading2(doc, "5.3   Database Schema")
add_body(doc, "The core database tables are defined as follows, cross-referenced with the architecture described in Section 5.2:")
schema_items = [
    "products (id, sku, name, quantity, reserved_quantity, created_at, updated_at)",
    "platform_credentials (id, platform, encrypted_api_key, refresh_token, token_expires_at)",
    "platform_listings (id, product_id, platform, platform_product_id, platform_variant_id, is_active)",
    "orders (id, platform, platform_order_id, product_id, quantity_ordered, status, received_at)",
    "sync_logs (id, order_id, target_platform, action, status, error_message, attempted_at)",
    "sync_tasks (id, task_type, payload_json, status, retry_count, next_retry_at, created_at)",
]
for item in schema_items:
    add_bullet(doc, item)

add_heading2(doc, "5.4   Inventory Synchronization Algorithm")
add_body(doc, "The following step-by-step algorithm governs each synchronization cycle:")
steps = [
    "Step 1:  Receive order event via platform webhook endpoint (FastAPI route).",
    "Step 2:  Validate HMAC/SHA-256 webhook signature; reject unauthenticated requests.",
    "Step 3:  Serialize order payload and push as a Celery task to the priority Redis queue.",
    "Step 4:  Celery worker picks task and opens a serializable PostgreSQL transaction.",
    "Step 5:  Execute SELECT * FROM products WHERE sku = ? FOR UPDATE (row-level lock).",
    "Step 6:  IF quantity >= ordered_quantity: deduct stock (UPDATE products SET quantity = quantity - ?).",
    "Step 7:  COMMIT transaction and release row lock.",
    "Step 8:  ELSE IF quantity < ordered_quantity: ROLLBACK; log oversell prevention event; halt.",
    "Step 9:  For each other connected platform, dispatch an async inventory update API call.",
    "Step 10: On API call failure, schedule retry with exponential backoff (1s, 2s, 4s, 8s … max 5 retries).",
    "Step 11: On max retries exceeded, route task to dead-letter queue and raise monitoring alert.",
    "Step 12: Log complete synchronization result (success/failure per platform) to sync_logs table.",
]
for step in steps:
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after  = Pt(3)
    run = p.add_run(step)
    run.font.name = FONT; run.font.size = Pt(11)
    run.font.name = "Courier New"; run.font.size = Pt(10)

# ══════════════════════════════════════════════
# 6. SUCCESS CRITERION
# ══════════════════════════════════════════════
add_heading1(doc, "6.   Success Criterion")
add_body(doc,
    "The project will be considered successful upon achieving all objectives defined in Section 3 "
    "through the following measurable and verifiable criteria:")
success = [
    "Functional Integration: The system successfully authenticates with and performs live inventory reads and writes on both Shopify Admin API and Amazon Selling Partner API.",
    "Oversell Prevention: During controlled testing with 50 simultaneous order placements targeting the same SKU across both platforms, zero overselling incidents occur and master inventory remains at exactly zero or greater.",
    "Synchronization Latency: Inventory updates propagate to all connected platforms within a maximum of 30 seconds under normal network conditions in at least 95% of test cases.",
    "Concurrency Safety: Row-level locking and atomic transactions prevent all race conditions; no duplicate stock deductions are observed during concurrent order simulations.",
    "Fault Tolerance: All failed API calls are automatically retried with exponential backoff; zero permanent failures occur on transient API errors within the 5-retry window.",
    "API Rate-Limit Compliance: API rate-limit violations remain below 2% of total calls during load testing, handled automatically by queue throttling.",
    "Monitoring Completeness: The admin dashboard displays accurate real-time synchronization status, with 100% of sync events traceable in the sync_logs table.",
    "Supervisor Acceptance: The completed system is reviewed and formally accepted by the project supervisor as satisfying all proposal objectives.",
]
for s in success:
    add_bullet(doc, s)

# ══════════════════════════════════════════════
# 7. TEAM ROLES AND RESPONSIBILITIES
# ══════════════════════════════════════════════
add_heading1(doc, "7.   Team Roles and Responsibilities")

add_body(doc,
    "The project is distributed across three team members with clearly defined, non-overlapping "
    "primary responsibilities. Table 1 presents the individual task allocation with tentative dates. "
    "Parallel and sequential task dependencies are managed as described in the Gantt chart in Figure 1.")

doc.add_paragraph()

# Table 1
task_caption = doc.add_paragraph("Table 1. Individual Task Allocation")
task_caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
for run in task_caption.runs:
    run.font.name = FONT; run.font.size = Pt(10); run.font.bold = True

task_table = doc.add_table(rows=19, cols=3)
task_table.style = "Table Grid"
task_table.alignment = WD_TABLE_ALIGNMENT.CENTER

headers_task = ["Team Member", "Activity", "Tentative Date"]
for j, h in enumerate(headers_task):
    set_cell_text(task_table.rows[0].cells[j], h, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
    shade_cell(task_table.rows[0].cells[j])

tasks = [
    # Member, Activity, Date
    ("Muhammad Hamza\n(FA23-BSE-111)\nDatabase & Backend Lead", "Requirement Analysis & API Documentation Study",             "Sep 2026"),
    ("",                                                          "Master Inventory Database Schema Design",                    "Oct 2026"),
    ("",                                                          "PostgreSQL Concurrency Control & Transaction Implementation", "Nov 2026"),
    ("",                                                          "Celery + Redis Queue System Setup & Configuration",          "Nov–Dec 2026"),
    ("",                                                          "Integration Testing (Inventory Logic & Concurrency)",        "Jan 2027"),
    ("",                                                          "Backend API Documentation & Technical Report Writing",       "Apr 2027"),
    ("Asadullah Naeem\n(FA23-BSE-041)\nAPI Integration Lead",    "Shopify Admin API Authentication & Integration",             "Oct–Nov 2026"),
    ("",                                                          "Amazon Selling Partner API Authentication & Integration",    "Nov–Dec 2026"),
    ("",                                                          "Webhook Endpoints & HMAC Signature Verification",            "Dec 2026"),
    ("",                                                          "Retry Mechanism & Dead-Letter Queue Implementation",         "Jan 2027"),
    ("",                                                          "Performance Testing, Load Testing & Optimization",           "Mar 2027"),
    ("",                                                          "Deployment & Cloud Infrastructure Configuration",            "Apr 2027"),
    ("Muhammad Sami\n(FA23-BSE-132)\nFrontend & Systems Lead",   "System Architecture Design & Diagram Production",            "Sep–Oct 2026"),
    ("",                                                          "Synchronization Engine Core Logic Development",              "Nov–Dec 2026"),
    ("",                                                          "React.js Admin Dashboard Development",                       "Jan–Feb 2027"),
    ("",                                                          "Logging, Monitoring Module & Alert System",                  "Feb 2027"),
    ("",                                                          "Load Testing Simulation & Concurrent Order Test Cases",      "Mar 2027"),
    ("",                                                          "Final Dissertation Writing & Presentation Preparation",      "Apr 2027"),
]

for i, (member, activity, date) in enumerate(tasks):
    set_cell_text(task_table.rows[i+1].cells[0], member)
    set_cell_text(task_table.rows[i+1].cells[1], activity)
    set_cell_text(task_table.rows[i+1].cells[2], date, align=WD_ALIGN_PARAGRAPH.CENTER)

doc.add_paragraph()

add_heading2(doc, "7.1   Task Execution Strategy")
add_body(doc, "Parallel Tasks:")
parallel = [
    "Database schema design and initial API integration research run concurrently from September–October 2026.",
    "Dashboard development begins in January 2027 while backend synchronization engine stabilizes.",
    "Load testing and final deployment preparation overlap during March–April 2027.",
]
for pt in parallel:
    add_bullet(doc, pt)

add_body(doc, "Sequential Dependencies:")
seq = [
    "Requirement analysis and API study must complete before system design begins.",
    "Database schema must be finalized before synchronization engine implementation.",
    "Synchronization engine must pass integration testing before load testing commences.",
    "Cloud deployment occurs only after all performance benchmarks are satisfied.",
]
for s in seq:
    add_bullet(doc, s)

add_heading2(doc, "7.2   Gantt Chart")
add_body(doc,
    "Figure 1 presents the project Gantt chart illustrating task durations, parallel execution tracks, "
    "and sequential dependencies across the eight-month development period from September 2026 to "
    "April 2027.")

# Gantt Chart as table
gantt_months = ["Sep\n2026", "Oct\n2026", "Nov\n2026", "Dec\n2026", "Jan\n2027", "Feb\n2027", "Mar\n2027", "Apr\n2027"]
gantt_tasks = [
    ("Req. Analysis & API Study",      [1,1,0,0,0,0,0,0]),
    ("Database Schema Design",         [0,1,1,0,0,0,0,0]),
    ("API Integration (Shopify)",      [0,1,1,0,0,0,0,0]),
    ("API Integration (Amazon SP)",    [0,0,1,1,0,0,0,0]),
    ("Webhook & Event Listeners",      [0,0,0,1,0,0,0,0]),
    ("Queue System (Celery+Redis)",    [0,0,1,1,0,0,0,0]),
    ("Sync Engine & Locking",          [0,0,1,1,0,0,0,0]),
    ("Retry & Dead-Letter Queue",      [0,0,0,0,1,0,0,0]),
    ("Admin Dashboard (React.js)",     [0,0,0,0,1,1,0,0]),
    ("Integration Testing",            [0,0,0,0,1,0,0,0]),
    ("Load & Performance Testing",     [0,0,0,0,0,0,1,0]),
    ("Deployment & Configuration",     [0,0,0,0,0,0,0,1]),
    ("Documentation & Dissertation",   [0,0,0,0,0,0,1,1]),
]

gantt_table = doc.add_table(rows=len(gantt_tasks)+1, cols=len(gantt_months)+1)
gantt_table.style = "Table Grid"

set_cell_text(gantt_table.rows[0].cells[0], "Task", bold=True, size=9)
shade_cell(gantt_table.rows[0].cells[0])
for j, m in enumerate(gantt_months):
    set_cell_text(gantt_table.rows[0].cells[j+1], m, bold=True, size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
    shade_cell(gantt_table.rows[0].cells[j+1])

for i, (task_name, months) in enumerate(gantt_tasks):
    set_cell_text(gantt_table.rows[i+1].cells[0], task_name, size=9)
    for j, active in enumerate(months):
        cell = gantt_table.rows[i+1].cells[j+1]
        if active:
            shade_cell(cell, "4472C4")
            set_cell_text(cell, "█", size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
        else:
            set_cell_text(cell, "", size=9)

gantt_cap = doc.add_paragraph("Figure 1. Project Gantt Chart (September 2026 – April 2027). Blue cells indicate active work periods.")
gantt_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
for run in gantt_cap.runs:
    run.font.name = FONT; run.font.size = Pt(10); run.font.italic = True

add_heading2(doc, "7.3   Justification of One-Year Effort")
add_body(doc,
    "The one-year development period is justified by the cumulative technical complexity of the "
    "project. Integration with two production-grade marketplace APIs (each requiring individual "
    "OAuth 2.0 flows, rate-limit management, and API-specific data transformations), the design "
    "and implementation of a distributed task queue with concurrency-safe stock deduction, "
    "real-time webhook infrastructure, comprehensive load and stress testing, cloud deployment, "
    "and full academic documentation constitutes substantial engineering effort commensurate with "
    "a three-member team working across two academic semesters.")

# ══════════════════════════════════════════════
# 8. TOOLS AND TECHNOLOGIES
# ══════════════════════════════════════════════
add_heading1(doc, "8.   Tools and Technologies")

tech_categories = [
    ("8.1   Backend Development",
     ["Python 3.11+ – Primary programming language",
      "FastAPI – Asynchronous REST API framework with built-in OpenAPI documentation",
      "Celery – Distributed task queue for background job processing",
      "SQLAlchemy – ORM for PostgreSQL database interaction and transaction management",
      "Pydantic – Data validation and serialization for API payloads"]),
    ("8.2   Database and Caching",
     ["PostgreSQL 15+ – Primary relational database (ACID-compliant, row-level locking support)",
      "Redis 7+ – In-memory data store for Celery broker, result backend, and rate-limit counters"]),
    ("8.3   Frontend Development",
     ["React.js 18+ – Administrative dashboard UI",
      "Axios – HTTP client for dashboard API communication"]),
    ("8.4   Integration and Authentication",
     ["Amazon Selling Partner API (SP-API) – Marketplace integration",
      "Shopify Admin API (REST + Webhooks) – Marketplace integration",
      "OAuth 2.0 – Authentication protocol for both marketplace integrations",
      "HMAC/SHA-256 – Webhook signature verification"]),
    ("8.5   Testing and Performance Evaluation",
     ["pytest – Python unit and integration testing framework",
      "Postman – API endpoint testing and webhook simulation",
      "Apache JMeter – Load testing and concurrent order simulation",
      "pytest-asyncio – Asynchronous test support for FastAPI endpoints"]),
    ("8.6   Deployment and Infrastructure",
     ["AWS EC2 / DigitalOcean – Cloud VPS hosting",
      "Docker – Containerization for consistent deployment environments",
      "Nginx – Reverse proxy and HTTPS termination",
      "GitHub Actions – CI/CD pipeline for automated testing and deployment",
      "Git & GitHub – Version control and collaborative development"]),
    ("8.7   Documentation and Project Management",
     ["Microsoft Word – Formal project documentation and dissertation",
      "GitHub Projects – Sprint planning and task tracking",
      "draw.io – Architecture and flow diagram creation"]),
]

for category, items in tech_categories:
    add_heading2(doc, category)
    for item in items:
        add_bullet(doc, item)

# ══════════════════════════════════════════════
# 9. REFERENCES (IEEE)
# ══════════════════════════════════════════════
add_heading1(doc, "9.   References")

references = [
    "[1]  S. Chopra and P. Meindl, Supply Chain Management: Strategy, Planning, and Operation, 6th ed. Boston, MA, USA: Pearson, 2016.",
    "[2]  A. S. Tanenbaum and M. Van Steen, Distributed Systems: Principles and Paradigms, 2nd ed. Upper Saddle River, NJ, USA: Prentice Hall, 2007.",
    "[3]  M. Fowler, Patterns of Enterprise Application Architecture. Boston, MA, USA: Addison-Wesley, 2002.",
    "[4]  H. Garcia-Molina, J. D. Ullman, and J. Widom, Database Systems: The Complete Book, 2nd ed. Upper Saddle River, NJ, USA: Prentice Hall, 2008.",
    "[5]  M. Kleppmann, Designing Data-Intensive Applications. Sebastopol, CA, USA: O'Reilly Media, 2017.",
    "[6]  Amazon, \"Selling Partner API Documentation,\" Amazon Developer Portal, 2024. [Online]. Available: https://developer.amazonservices.com. [Accessed: Mar. 5, 2026].",
    "[7]  Shopify, \"Webhook and Admin API Documentation,\" Shopify Developers, 2024. [Online]. Available: https://shopify.dev. [Accessed: Mar. 5, 2026].",
    "[8]  eBay Inc., \"eBay Developer Program API Documentation,\" 2024. [Online]. Available: https://developer.ebay.com. [Accessed: Mar. 5, 2026].",
    "[9]  R. T. Fielding, \"Architectural Styles and the Design of Network-Based Software Architectures,\" Doctoral dissertation, University of California, Irvine, CA, USA, 2000.",
    "[10] G. DeCandia et al., \"Dynamo: Amazon's Highly Available Key-Value Store,\" in Proc. 21st ACM Symp. Operating Systems Principles (SOSP), Stevenson, WA, USA, 2007, pp. 205–220.",
]
for ref in references:
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after  = Pt(4)
    p.paragraph_format.left_indent  = Inches(0.3)
    p.paragraph_format.first_line_indent = Inches(-0.3)
    run = p.add_run(ref)
    run.font.name = FONT; run.font.size = Pt(11)

doc.add_page_break()

# ══════════════════════════════════════════════
# APPENDIX A
# ══════════════════════════════════════════════
add_heading1(doc, "Appendix A – Turnitin Similarity Report")
add_body(doc, "Include here the 1st page of the Turnitin Report (MANDATORY).")

doc.add_page_break()

# ══════════════════════════════════════════════
# APPENDIX B
# ══════════════════════════════════════════════
add_heading1(doc, "Appendix B – AI Detection Report")
add_body(doc, "Include here the 1st page of the AI Report generated through Turnitin (MANDATORY).")

# ──────────────────────────────────────────────
# SAVE
# ──────────────────────────────────────────────
output_path = r"e:\FYP\FYP_Proposal_Final.docx"
doc.save(output_path)
print(f"SUCCESS: Proposal saved to {output_path}")
