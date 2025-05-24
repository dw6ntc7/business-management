#!/usr/bin/env python3
"""
Test script to verify the streamlined PDF templates work correctly
"""

from app import app, db, Offer, Invoice, Customer, CompanySettings, PdfTemplate
from flask import render_template_string

def test_templates():
    with app.app_context():
        # Get test data
        offer = Offer.query.first()
        invoice = Invoice.query.first()
        company = CompanySettings.query.first()
        
        if not offer or not invoice:
            print("❌ No test data found. Creating sample data...")
            return
            
        print("🔍 Testing streamlined templates...")
        
        # Test Offer Template
        print("\n📄 Testing Offer Template:")
        offer_template = PdfTemplate.query.filter_by(name="Angebot").first()
        if offer_template:
            try:
                rendered_offer = render_template_string(offer_template.content, offer=offer, company=company)
                print(f"✅ Offer template rendered successfully ({len(rendered_offer)} characters)")
                print(f"   Template size: {len(offer_template.content)} characters")
                
                # Check for key components
                checks = [
                    ("{% extends 'base.html' %}", "Base template extension"),
                    ("{% from 'pdf_macros.html'", "Macro imports"),
                    ("pdf-styles.css", "CSS stylesheet"),
                    ("pdf-utils.js", "JavaScript utilities"),
                    ("company_info_card", "Company info macro"),
                    ("customer_info_card", "Customer info macro"),
                    ("positions_table", "Positions table macro"),
                    ("action_buttons", "Action buttons macro")
                ]
                
                for check, description in checks:
                    if check in offer_template.content:
                        print(f"   ✅ {description}")
                    else:
                        print(f"   ❌ {description}")
                        
            except Exception as e:
                print(f"❌ Error rendering offer template: {e}")
        else:
            print("❌ Offer template not found in database")
            
        # Test Invoice Template
        print("\n📄 Testing Invoice Template:")
        invoice_template = PdfTemplate.query.filter_by(name="Rechnung").first()
        if invoice_template:
            try:
                rendered_invoice = render_template_string(invoice_template.content, invoice=invoice, company=company)
                print(f"✅ Invoice template rendered successfully ({len(rendered_invoice)} characters)")
                print(f"   Template size: {len(invoice_template.content)} characters")
                
                # Check for key components
                if "qr_code_section" in invoice_template.content:
                    print("   ✅ QR code section (for payments)")
                else:
                    print("   ❌ QR code section missing")
                    
            except Exception as e:
                print(f"❌ Error rendering invoice template: {e}")
        else:
            print("❌ Invoice template not found in database")
            
        # Compare with original backup templates
        print("\n📊 Size Comparison with Originals:")
        try:
            with open('/home/matthias/trysqlite/angebot_template.html', 'r', encoding='utf-8') as f:
                original_offer_size = len(f.read())
            print(f"   Original Offer: {original_offer_size:,} characters")
            print(f"   Streamlined:    {len(offer_template.content):,} characters")
            reduction = ((original_offer_size - len(offer_template.content)) / original_offer_size) * 100
            print(f"   Reduction:      {reduction:.1f}%")
        except:
            print("   Could not compare offer template sizes")
            
        try:
            with open('/home/matthias/trysqlite/rechnung_template.html', 'r', encoding='utf-8') as f:
                original_invoice_size = len(f.read())
            print(f"   Original Invoice: {original_invoice_size:,} characters")
            print(f"   Streamlined:      {len(invoice_template.content):,} characters")
            reduction = ((original_invoice_size - len(invoice_template.content)) / original_invoice_size) * 100
            print(f"   Reduction:        {reduction:.1f}%")
        except:
            print("   Could not compare invoice template sizes")

if __name__ == '__main__':
    test_templates()
