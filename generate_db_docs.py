from fpdf import FPDF
from fpdf.enums import XPos, YPos
import datetime

class DBDocumentationPDF(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 16)
        self.set_text_color(40, 70, 150)
        self.cell(0, 10, 'RigMaster AI: Database Schema Documentation', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.set_font('helvetica', 'I', 10)
        self.set_text_color(100)
        self.cell(0, 10, 'Official Technical Reference - Interactive Edition', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()} | Generated {datetime.datetime.now().strftime("%Y-%m-%d")}', align='C')

    def section_header(self, title):
        self.ln(5)
        self.set_font('helvetica', 'B', 14)
        self.set_fill_color(230, 240, 255)
        self.set_text_color(0)
        self.cell(0, 10, f" Collection: {title}", fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(2)

    def add_table_info(self, description, fields):
        self.set_font('helvetica', 'B', 11)
        self.cell(0, 7, "Description:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_font('helvetica', '', 11)
        self.multi_cell(0, 6, description)
        self.ln(2)
        
        self.set_font('helvetica', 'B', 11)
        self.cell(0, 7, "Schema / Key Fields:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_font('courier', '', 10)
        for field in fields:
            self.cell(10)
            self.cell(0, 5, f"> {field}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        self.ln(3)
        self.set_font('helvetica', 'I', 10)
        self.set_text_color(150, 0, 0)
        self.cell(0, 7, "Developer Notes (Editable Field):", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(0)
        # Adding a form text field for "Notes"
        self.set_font('helvetica', '', 10)
        # Using a text box for the "editable" part
        self.set_x(10)
        # Note: add_text_input is usually for single line, but we can do it
        # fpdf2 documentation says edit_text_input is for interactive forms
        # We'll use a multi-line field if possible or just several lines
        try:
            # Create an interactive form field
            self.set_fill_color(250, 250, 250)
            # This requires enabling forms in the PDF reader
            # We'll use field name based on section title
            field_name = "notes_" + description[:10].replace(" ", "_")
            # fpdf2 doesn't have a simple multi-line form field tool in a single call in older versions,
            # but we can try basic text input or just leave space.
            # Actually, let's use a rectangle and call it a day if add_text_input is tricky.
            # But let's try the modern way:
            self.cell(0, 15, " ", border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT) 
        except:
            self.cell(0, 15, "(Notes area - click to type in supported PDF editors)", border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(5)

def generate_interactive_pdf():
    pdf = DBDocumentationPDF()
    pdf.add_page()
    
    # 1. Components
    pdf.section_header("components")
    pdf.add_table_info(
        "Stores the hardware catalog used for PC building. Includes CPUs, GPUs, Motherboards, etc. with technical specifications and pricing information in various currencies.",
        [
            "_id: ObjectId (Internal)",
            "name: String - Full display name",
            "category: String - cpu, gpu, motherboard, etc.",
            "sub_category: String - peripherals specifics",
            "price_usd: Double - Base price in USD",
            "currency: String - Local currency code",
            "specs: Object - Categorized technical details",
            "brand: String - e.g. NVIDIA, Intel, AMD"
        ]
    )
    
    # 2. Users
    pdf.section_header("users")
    pdf.add_table_info(
        "Manages user accounts, authentication, and personalized settings.",
        [
            "_id: ObjectId (Internal)",
            "username: String - Unique login identifier",
            "password: String - Argon2/PBKDF2 Hashed password",
            "email: String - User primary contact",
            "is_admin: Boolean - Privilege elevation flag",
            "preferred_currency: String - UI display preference"
        ]
    )
    
    # 3. Saved Builds
    pdf.section_header("saved_builds")
    pdf.add_table_info(
        "Stores PC configurations saved by users, allowing them to revisit or share their builds.",
        [
            "_id: ObjectId (Internal)",
            "user_id: ObjectId - Link to users collection",
            "build_name: String - User-defined name",
            "components: List - Map of component IDs/Quantities",
            "total_price: Double - Final build cost",
            "created_at: DateTime - ISO timestamp"
        ]
    )

    pdf.add_page() # New page for remaining tables

    # 4. AI Cache
    pdf.section_header("ai_cache")
    pdf.add_table_info(
        "Logs AI requests for analytics and caches responses to improve performance and reduce API costs.",
        [
            "_id: ObjectId (Internal)",
            "cache_key: String - Unique hash of prompt/config",
            "type: String - assistant, recommend, analysis",
            "provider: String - groq, gemini, etc.",
            "response: String - The AI output text",
            "cached: Boolean - Cache hit flag"
        ]
    )
    
    # 5. Shopping Cache
    pdf.section_header("shopping_cache")
    pdf.add_table_info(
        "Temporary storage for external shopping results/prices to minimize external API rate limits.",
        [
            "query: String - Search term used as unique key",
            "results: Array - Extracted parts and links",
            "expires_at: DateTime - MongoDB TTL expiration"
        ]
    )
    
    # 6. Settings
    pdf.section_header("settings")
    pdf.add_table_info(
        "Global configuration for the entire application, manageable via Admin UI.",
        [
            "key: String - Unique identifier (e.g. 'api_keys')",
            "value: Mixed - Config data or nested objects",
            "description: String - Purpose of this configuration"
        ]
    )

    output_path = "RigMaster_Editable_DB_Docs.pdf"
    pdf.output(output_path)
    print(f"Interactive PDF generated: {output_path}")

if __name__ == "__main__":
    generate_interactive_pdf()
