from enum import Enum


class Location(str, Enum):
    COSTA_RICA = "Costa Rica"
    LATAM = "LATAM"


class WorkMode(str, Enum):
    REMOTE = "Remote"
    HYBRID = "Hybrid"
    ONSITE = "Onsite"


class EmploymentType(str, Enum):
    FULL_TIME = "Full-time"
    PART_TIME = "Part-time"
    CONTRACT = "Contract"
    FREELANCE = "Freelance"
    TEMPORARY = "Temporary"
    INTERNSHIP = "Internship"


class ExperienceLevel(str, Enum):
    ENTRY_LEVEL = "Entry-level"
    JUNIOR = "Junior"
    MID_LEVEL = "Mid-level"
    SENIOR = "Senior"
    LEAD = "Lead"
    PRINCIPAL = "Principal"
    EXECUTIVE = "Executive"


class JobFunction(str, Enum):
    TECHNOLOGY_ENGINEERING = "Technology & Engineering"
    SALES_BUSINESS_DEVELOPMENT = "Sales & Business Development"
    MARKETING_COMMUNICATIONS = "Marketing & Communications"
    OPERATIONS_LOGISTICS = "Operations & Logistics"
    FINANCE_ACCOUNTING = "Finance & Accounting"
    HUMAN_RESOURCES = "Human Resources"
    CUSTOMER_SUCCESS_SUPPORT = "Customer Success & Support"
    PRODUCT_MANAGEMENT = "Product Management"
    DATA_ANALYTICS = "Data & Analytics"
    HEALTHCARE_MEDICAL = "Healthcare & Medical"
    LEGAL_COMPLIANCE = "Legal & Compliance"
    DESIGN_CREATIVE = "Design & Creative"
    ADMINISTRATIVE_OFFICE = "Administrative & Office"
    CONSULTING_STRATEGY = "Consulting & Strategy"
    GENERAL_MANAGEMENT = "General Management"
    OTHER = "Other"


class Province(str, Enum):
    SAN_JOSE = "San Jose"
    ALAJUELA = "Alajuela"
    HEREDIA = "Heredia"
    GUANACASTE = "Guanacaste"
    PUNTARENAS = "Puntarenas"
    LIMON = "Limon"
    CARTAGO = "Cartago"
