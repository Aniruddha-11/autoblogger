from datetime import datetime

class ProductKnowledgeModel:
    @staticmethod
    def get_default_product_knowledge():
        """Get default Smart Weld product knowledge"""
        return {
            "company_name": "Smart Weld",
            "main_website": "https://www.smart-weld.com/",
            "brochure_link": "https://www.smart-weld.com/brochure",
            "benefits_link": "https://www.smart-weld.com/benefits",
            "phone_number": "(+91) 94346-41479",
            "product_features": [
                "Automated precision welding technology",
                "Real-time monitoring and quality control",
                "AI-powered defect detection",
                "Industry 4.0 integration capabilities",
                "Reduced operational costs by up to 40%",
                "Compatible with MIG, TIG, and Arc welding processes"
            ],
            "target_industries": [
                "Automotive manufacturing",
                "Aerospace",
                "Shipbuilding",
                "Pipeline construction",
                "Heavy machinery",
                "Underwater welding operations"
            ],
            "unique_selling_points": [
                "Patented smart sensor technology",
                "Cloud-based analytics dashboard",
                "24/7 remote monitoring",
                "Predictive maintenance alerts",
                "ISO 9001 and AWS certified"
            ],
            "cta_templates": [
                "Transform your welding operations with Smart Weld's cutting-edge technology. Call us at {phone} or download our comprehensive brochure at {brochure_link} to learn how we can help you achieve superior weld quality while reducing costs.",
                "Ready to revolutionize your welding process? Smart Weld offers intelligent solutions tailored to your industry needs. Contact us at {phone} or visit {main_link} to schedule a free consultation.",
                "Discover why leading manufacturers trust Smart Weld for their automated welding needs. Get your free consultation at {phone} or explore our benefits at {benefits_link}."
            ]
        }