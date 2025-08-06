import re
import json
from typing import Dict, Optional, List
from collections import defaultdict
from core.database import Session, Category, Subcategory, BankTransaction
from core.repository.TransactionRepository import TransactionRepository
from config.settings import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_ENABLE_CATEGORIZATION


class CategorizationService:
    """Service for automatic transaction categorization."""

    def __init__(self):
        self.session = Session()
        
        # Initialize OpenAI client if configured
        self.openai_client = None
        self.openai_enabled = False
        
        if OPENAI_ENABLE_CATEGORIZATION and OPENAI_API_KEY:
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
                self.openai_enabled = True
                print("✓ OpenAI client initialized for transaction categorization")
            except ImportError:
                print("⚠️  OpenAI package not available. Falling back to keyword-based categorization.")
            except Exception as e:
                print(f"⚠️  Failed to initialize OpenAI client: {e}. Falling back to keyword-based categorization.")

        # Define keyword patterns for categorization
        self.category_keywords = {
            "Food & Dining": [
                r'\b(restaurant|cafe|coffee|mcdonald|kfc|pizza|bakery|resto|warung|makan|nasi|ayam|soto|gado|rendang|padang|chinese|japanese|korean|thai|indian|western|buffet|catering|delivery|gofood|grabfood|shopeefood|foodpanda)\b',
                r'\b(food|dining|lunch|dinner|breakfast|snack|drink|beverage|starbucks|dunkin|chatime|koi|teh|jco|breadtalk|hokben|yoshinoya|pepper|solaria|es teler|martabak|bakso|mie ayam)\b',
                r'\b(supermarket|hypermarket|alfamart|indomaret|carrefour|giant|hero|ranch market|farmers market|total buah|sayur|daging|ikan|beras|minyak|gula|tepung|susu|telur)\b'
            ],
            "Transportation": [
                r'\b(taxi|grab|gojek|uber|ojek|angkot|bus|kereta|mrt|lrt|transjakarta|damri|travel|rental|sewa|mobil|motor|bensin|pertamax|solar|parkir|tol|e-toll|mandiri e-toll)\b',
                r'\b(garasi|bengkel|service|oli|ban|aki|sparepart|otomotif|honda|toyota|yamaha|suzuki|kawasaki|daihatsu|mitsubishi|nissan|ford|chevrolet)\b',
                r'\b(fuel|gas|gasoline|petrol|diesel|premium|pertalite|dexlite|biosolar|bbm|spbu|shell|bp|total|vivo|esso)\b'
            ],
            "Shopping": [
                r'\b(mall|plaza|shopping|store|toko|shop|market|pasar|department|boutique|fashion|clothing|baju|celana|sepatu|tas|jam|aksesoris|kosmetik|parfum|skincare)\b',
                r'\b(tokopedia|shopee|lazada|blibli|bukalapak|zalora|jd\.id|elevenia|orami|sociolla|female daily|zilingo|bhinneka|amazon|alibaba|ebay)\b',
                r'\b(elektronik|gadget|laptop|hp|smartphone|tablet|tv|kulkas|ac|mesin cuci|kompor|setrika|vacuum|printer|kamera|headphone|speaker)\b'
            ],
            "Health & Fitness": [
                r'\b(hospital|rumah sakit|rs|klinik|clinic|dokter|doctor|medical|kesehatan|obat|pharmacy|apotek|kimia farma|guardian|watson|century|viva)\b',
                r'\b(gym|fitness|olahraga|sport|yoga|pilates|zumba|senam|renang|tennis|badminton|football|basket|volleyball|golf|boxing|martial arts)\b',
                r'\b(vitamin|supplement|protein|medicine|tablet|kapsul|sirup|salep|plester|termometer|masker|hand sanitizer|antiseptic)\b'
            ],
            "Entertainment": [
                r'\b(cinema|bioskop|xxi|cgv|cineplex|movie|film|theater|concert|konser|musik|netflix|spotify|youtube|disney|hbo|amazon prime|apple tv)\b',
                r'\b(game|gaming|steam|playstation|xbox|nintendo|mobile legend|pubg|free fire|valorant|dota|genshin|among us|roblox|minecraft)\b',
                r'\b(book|buku|gramedia|kinokuniya|periplus|togamas|library|perpustakaan|novel|komik|manga|magazine|majalah|koran|newspaper)\b'
            ],
            "Personal Care": [
                r'\b(salon|barbershop|pangkas|potong|rambut|hair|nail|kuku|spa|massage|facial|treatment|kecantikan|beauty|salon kecantikan)\b',
                r'\b(shampoo|conditioner|sabun|pasta gigi|sikat gigi|deodorant|cologne|lotion|cream|serum|toner|cleanser|moisturizer|sunscreen)\b'
            ],
            "Bills & Utilities": [
                r'\b(listrik|pln|gas|pdam|air|telepon|telkom|indihome|internet|wifi|tv kabel|first media|biznet|mnc|transvision|k-vision)\b',
                r'\b(pajak|tax|pbb|bphtb|stnk|sim|bpjs|insurance|asuransi|premi|iuran|membership|langganan|subscription|netflix|spotify)\b',
                r'\b(bank|atm|admin|administration|biaya admin|transfer|transfer fee|bunga|interest|denda|penalty|maintenance fee)\b'
            ],
            "Transfers & Banking": [
                r'\b(transfer|kirim|send|tarik|withdraw|setor|deposit|nabung|saving|investasi|investment|reksadana|saham|obligasi|deposito)\b',
                r'\b(atm|mobile banking|internet banking|m-banking|sms banking|phone banking|teller|cs|customer service)\b'
            ],
            "Income": [
                r'\b(gaji|salary|bonus|thr|insentif|incentive|komisi|commission|honorarium|fee|upah|pendapatan|income|revenue|profit|dividen)\b',
                r'\b(freelance|konsultan|consultant|jasa|service|project|kontrak|contract|royalty|patent|copyright|licensing)\b'
            ],
            "Education": [
                r'\b(sekolah|school|universitas|university|kuliah|college|kursus|course|les|tutorial|training|seminar|workshop|conference)\b',
                r'\b(spp|uang sekolah|tuition|buku|book|alat tulis|stationery|laptop|uniform|seragam|tas sekolah|sepatu sekolah)\b'
            ],
            "Travel": [
                r'\b(hotel|resort|villa|penginapan|homestay|airbnb|agoda|traveloka|tiket|ticket|pesawat|airplane|garuda|lion|citilink|airasia)\b',
                r'\b(wisata|tour|travel|liburan|vacation|holiday|trip|backpack|guide|pemandu|souvenir|oleh-oleh|gift|hadiah)\b'
            ]
        }

    def _get_available_categories(self) -> Dict[str, List[str]]:
        """Get all available categories and subcategories from the database."""
        categories = self.session.query(Category).filter(Category.deleted_at.is_(None)).all()
        
        category_structure = {}
        for category in categories:
            subcategories = self.session.query(Subcategory).filter(
                Subcategory.category_id == category.id,
                Subcategory.deleted_at.is_(None)
            ).all()
            category_structure[category.name] = [sub.name for sub in subcategories]
        
        return category_structure

    def _categorize_with_openai(self, description: str) -> Optional[Dict[str, any]]:
        """
        Use OpenAI to categorize a transaction based on its description.
        
        Returns:
            Dict with category_id and subcategory_id, or None if categorization fails
        """
        if not self.openai_enabled or not self.openai_client:
            return None
            
        try:
            # Get available categories
            categories = self._get_available_categories()
            
            # Create prompt for OpenAI
            prompt = f"""
You are a financial transaction categorizer. Given a transaction description, categorize it into one of the available categories and subcategories.

Available categories and subcategories:
{json.dumps(categories, indent=2)}

Transaction description: "{description}"

Please respond with a JSON object containing:
- "category": the main category name (exactly as shown above)
- "subcategory": the subcategory name (exactly as shown above, or null if no suitable subcategory)
- "confidence": confidence score between 0.0 and 1.0

If you cannot confidently categorize the transaction, respond with null.

Example response:
{{"category": "Food & Dining", "subcategory": "Restaurants", "confidence": 0.9}}
"""

            response = self.openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful financial transaction categorizer. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=150
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Parse JSON response
            try:
                result = json.loads(result_text)
                if result is None:
                    return None
                    
                category_name = result.get('category')
                subcategory_name = result.get('subcategory')
                confidence = result.get('confidence', 0.0)
                
                # Validate and get category from database
                if category_name:
                    category = self.session.query(Category).filter(
                        Category.name == category_name,
                        Category.deleted_at.is_(None)
                    ).first()
                    
                    if category:
                        subcategory = None
                        if subcategory_name:
                            subcategory = self.session.query(Subcategory).filter(
                                Subcategory.name == subcategory_name,
                                Subcategory.category_id == category.id,
                                Subcategory.deleted_at.is_(None)
                            ).first()
                        
                        return {
                            'category_id': category.id,
                            'subcategory_id': subcategory.id if subcategory else None,
                            'category_name': category_name,
                            'subcategory_name': subcategory_name if subcategory else None,
                            'confidence': confidence,
                            'method': 'openai'
                        }
                        
            except json.JSONDecodeError:
                print(f"⚠️  Failed to parse OpenAI response as JSON: {result_text}")
                return None
                
        except Exception as e:
            print(f"⚠️  OpenAI categorization failed: {e}")
            return None
            
        return None

    def categorize_transaction(self, description: str) -> Optional[Dict[str, any]]:
        """
        Categorize a transaction based on its description.
        Uses OpenAI if configured, otherwise falls back to keyword-based categorization.

        Returns:
            Dict with category_id and subcategory_id, or None if no match
        """
        if not description:
            return None

        # Try OpenAI categorization first if enabled
        if self.openai_enabled:
            openai_result = self._categorize_with_openai(description)
            if openai_result:
                return openai_result

        # Fallback to keyword-based categorization
        return self._categorize_with_keywords(description)

    def _categorize_with_keywords(self, description: str) -> Optional[Dict[str, any]]:
        """
        Categorize a transaction using keyword-based pattern matching.
        
        Returns:
            Dict with category_id and subcategory_id, or None if no match
        """
        description_lower = description.lower()

        # Try to match against category keywords
        for category_name, patterns in self.category_keywords.items():
            for pattern in patterns:
                if re.search(pattern, description_lower, re.IGNORECASE):
                    # Get category from database
                    category = self.session.query(Category).filter(
                        Category.name == category_name,
                        Category.deleted_at.is_(None)
                    ).first()

                    if category:
                        # Try to find a more specific subcategory
                        subcategory = self._find_subcategory(description_lower, category.id)

                        return {
                            'category_id': category.id,
                            'subcategory_id': subcategory.id if subcategory else None,
                            'category_name': category_name,
                            'subcategory_name': subcategory.name if subcategory else None,
                            'method': 'keywords'
                        }

        return None

    def _find_subcategory(self, description: str, category_id: int) -> Optional[Subcategory]:
        """Find the most appropriate subcategory for a transaction."""
        subcategories = self.session.query(Subcategory).filter(
            Subcategory.category_id == category_id,
            Subcategory.deleted_at.is_(None)
        ).all()

        # Define subcategory-specific keywords
        subcategory_keywords = {
            # Food & Dining subcategories
            "Restaurants": [r'\b(restaurant|resto|dining|fine dining|casual dining)\b'],
            "Fast Food": [r'\b(mcdonald|kfc|burger|pizza|fast food|quick service)\b'],
            "Coffee & Beverages": [r'\b(coffee|cafe|starbucks|dunkin|tea|beverage|drink|chatime|koi)\b'],
            "Groceries & Supermarkets": [r'\b(supermarket|hypermarket|alfamart|indomaret|carrefour|giant|grocery)\b'],
            "Street Food": [r'\b(warung|pedagang|street|jajanan|gorengan|bakso|mie ayam)\b'],

            # Transportation subcategories
            "Public Transport": [r'\b(bus|kereta|mrt|lrt|transjakarta|angkot|public)\b'],
            "Taxi & Ride Sharing": [r'\b(taxi|grab|gojek|uber|ojek|ride)\b'],
            "Fuel": [r'\b(bensin|pertamax|solar|fuel|gas|spbu|shell|bp)\b'],
            "Parking": [r'\b(parkir|parking|park)\b'],
            "Vehicle Maintenance": [r'\b(bengkel|service|oli|ban|maintenance|repair)\b'],

            # Shopping subcategories
            "Online Shopping": [r'\b(tokopedia|shopee|lazada|blibli|online|e-commerce)\b'],
            "Electronics": [r'\b(laptop|hp|smartphone|tv|elektronik|gadget)\b'],
            "Clothing & Fashion": [r'\b(baju|celana|sepatu|fashion|clothing|boutique)\b'],
        }

        for subcategory in subcategories:
            patterns = subcategory_keywords.get(subcategory.name, [])
            for pattern in patterns:
                if re.search(pattern, description, re.IGNORECASE):
                    return subcategory

        return None

    def auto_categorize_transactions(self, user_id: int, batch_size: int = 100) -> Dict[str, int]:
        """
        Auto-categorize all uncategorized transactions for a user.

        Returns:
            Dict with categorization statistics
        """
        from core.repository.BankAccountRepository import BankAccountRepository

        account_repo = BankAccountRepository(self.session)
        account = account_repo.get_by_telegram_id(str(user_id))

        if not account:
            return {'error': 'Account not found'}

        # Get uncategorized transactions using direct session query
        uncategorized_transactions = self.session.query(BankTransaction).filter(
            BankTransaction.user_id == account.id,
            BankTransaction.category_id.is_(None),
            BankTransaction.deleted_at.is_(None)
        ).limit(batch_size).all()

        stats = {
            'total_processed': 0,
            'successfully_categorized': 0,
            'failed_categorization': 0,
            'openai_categorized': 0,
            'keyword_categorized': 0,
            'categories_assigned': defaultdict(int)
        }

        for transaction in uncategorized_transactions:
            stats['total_processed'] += 1

            categorization = self.categorize_transaction(transaction.description)

            if categorization:
                # Update the transaction with category information
                transaction.category_id = categorization['category_id']
                transaction.subcategory_id = categorization['subcategory_id']

                stats['successfully_categorized'] += 1
                stats['categories_assigned'][categorization['category_name']] += 1
                
                # Track categorization method
                method = categorization.get('method', 'unknown')
                if method == 'openai':
                    stats['openai_categorized'] += 1
                elif method == 'keywords':
                    stats['keyword_categorized'] += 1
            else:
                stats['failed_categorization'] += 1

        # Commit changes
        self.session.commit()

        return dict(stats)

    def get_categorization_statistics(self, user_id: int) -> Dict[str, any]:
        """Get categorization statistics for a user."""
        from core.repository.BankAccountRepository import BankAccountRepository

        account_repo = BankAccountRepository(self.session)
        account = account_repo.get_by_telegram_id(str(user_id))

        if not account:
            return {'error': 'Account not found'}

        # Use direct session queries instead of repository.session
        total_transactions = self.session.query(BankTransaction).filter(
            BankTransaction.user_id == account.id,
            BankTransaction.deleted_at.is_(None)
        ).count()

        categorized_transactions = self.session.query(BankTransaction).filter(
            BankTransaction.user_id == account.id,
            BankTransaction.category_id.is_not(None),
            BankTransaction.deleted_at.is_(None)
        ).count()

        uncategorized_transactions = total_transactions - categorized_transactions

        categorization_rate = (categorized_transactions / total_transactions * 100) if total_transactions > 0 else 0

        return {
            'total_transactions': total_transactions,
            'categorized_transactions': categorized_transactions,
            'uncategorized_transactions': uncategorized_transactions,
            'categorization_rate': categorization_rate
        }

    def __del__(self):
        """Close the session when the service is destroyed."""
        if hasattr(self, 'session'):
            self.session.close()