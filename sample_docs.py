"""Built-in demo knowledge base so the app works out of the box."""

SAMPLE_DOCS = {
    "employee_handbook.txt": """
Leave Policy. Every full-time employee is entitled to 24 days of paid annual leave per calendar year.
Up to 8 unused leave days can be carried forward to the next year. Employees also receive 12 days of
sick leave; a medical certificate is required for sick leave longer than 3 consecutive days.
Maternity leave is 26 weeks and paternity leave is 15 working days.

Work From Home. Employees may work from home up to 2 days per week with manager approval.
Requests must be raised in the HR portal at least 24 hours in advance. Core collaboration hours are
11 AM to 4 PM IST, during which employees must be reachable on the company chat tool.

Learning & Development. The company reimburses up to Rs. 40,000 per year for approved certifications
such as AWS, Azure, Google Cloud, PMP or data science courses. Employees must submit the certificate and
invoice within 30 days of completion. Internal tech talks happen every Friday at 4 PM.
""",
    "it_security_policy.txt": """
Password Policy. Passwords must be at least 12 characters and include upper case, lower case, a number
and a symbol. Passwords expire every 90 days and the last 5 passwords cannot be reused.
Multi-factor authentication (MFA) is mandatory for email, VPN and all cloud consoles.

Data Handling. Customer data is classified as Confidential and must never be stored on personal devices
or shared through personal email. Laptops use full-disk encryption. Lost or stolen devices must be
reported to the IT helpdesk within 2 hours. Phishing emails should be reported using the
"Report Phish" button; never click unknown links.

Software. Only software from the approved catalogue may be installed. Requests for new tools go through
the IT service desk and are reviewed by the security team within 3 business days.
""",
    "product_faq.txt": """
What is CloudDesk? CloudDesk is our AI-powered help-desk platform that automates ticket routing,
suggests answers using retrieval-augmented generation and provides analytics dashboards.
Pricing: the Starter plan costs Rs. 999 per agent per month, Growth costs Rs. 2,499 and Enterprise is
custom priced. All plans include a 14-day free trial with no credit card required.
Integrations: CloudDesk integrates with Slack, Microsoft Teams, WhatsApp Business, Gmail and Jira.
Support: Starter plans get email support within 24 hours; Growth and Enterprise get 24x7 chat support
and a dedicated customer success manager for Enterprise.
""",
}

SAMPLE_QUESTIONS = [
    "How many days of annual leave can I carry forward?",
    "What is the password policy?",
    "How much does the Growth plan cost?",
    "What should I do if my laptop is stolen?",
]
