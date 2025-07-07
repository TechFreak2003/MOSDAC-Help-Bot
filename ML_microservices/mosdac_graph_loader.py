import os
import json
from datetime import datetime, timezone
import asyncio
from dotenv import load_dotenv
from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType
from neo4j import GraphDatabase

# Load Neo4j credentials from .env
load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

# Path to scraped data directory
DATA_DIR = "E:\\Bharatiya Antariksh Hackathon-2025\\Code1\\Scrapper\\data"

# Dataset files mapping
DATASETS = {
    "satellites": "satellites.json",
    "products": "products.json", 
    "documents": "documents.json",
    "mission_metadata": "mission_metadata.json",
    "faqs": "faqs.json"
}

class MOSDACGraphLoader:
    def __init__(self):
        # Initialize Graphiti with standard parameters
        self.graphiti = Graphiti(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
        self.reference_time = datetime.now(timezone.utc)
        self.driver = None
        self.using_default_db = False
    
    async def setup_neo4j_database(self):
        """Setup Neo4j database connection and ensure proper database exists"""
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        
        try:
            print("🔍 Checking Neo4j database setup...")
            
            with self.driver.session() as session:
                # Check Neo4j version and edition
                try:
                    version_result = session.run("CALL dbms.components() YIELD name, versions, edition RETURN name, versions[0] as version, edition")
                    neo4j_edition = "Community"
                    for record in version_result:
                        if record["name"] == "Neo4j Kernel":
                            neo4j_edition = record["edition"]
                            print(f"📋 Neo4j Version: {record['version']} ({neo4j_edition})")
                except Exception as e:
                    print(f"⚠️  Could not get version info: {str(e)}")
                    neo4j_edition = "Community"
                
                # Check available databases
                try:
                    result = session.run("SHOW DATABASES")
                    databases = [record["name"] for record in result]
                    print(f"📋 Available databases: {databases}")
                    
                    # Try different approaches to create default_db
                    if "default_db" not in databases:
                        print("🏗️  Creating 'default_db' database (required by Graphiti)...")
                        success = await self._try_create_database(session)
                        if success:
                            return True
                    else:
                        print("✅ Database 'default_db' already exists!")
                        return True
                        
                except Exception as show_error:
                    error_msg = str(show_error).lower()
                    if "unsupported" in error_msg or "procedure" in error_msg:
                        print("⚠️  Multi-database features not available (Neo4j Community Edition)")
                        return self._handle_community_edition(session)
                    else:
                        print(f"❌ Error with database commands: {str(show_error)}")
                        return self._handle_community_edition(session)
            
            return True
            
        except Exception as e:
            print(f"❌ Error setting up Neo4j database: {str(e)}")
            print("💡 Common solutions:")
            print("   - Check if Neo4j is running on localhost:7687")
            print("   - Verify credentials in .env file")
            print("   - Try connecting to the default database")
            return False
    
    async def _try_create_database(self, session):
        """Try multiple methods to create the default_db database"""
        methods = [
            # Method 1: With backticks
            "CREATE DATABASE `default_db`",
            # Method 2: Without backticks
            "CREATE DATABASE default_db",
            # Method 3: With single quotes
            "CREATE DATABASE 'default_db'",
            # Method 4: With double quotes
            'CREATE DATABASE "default_db"'
        ]
        
        for i, method in enumerate(methods, 1):
            try:
                print(f"   Attempt {i}: {method}")
                session.run(method)
                print("✅ Database 'default_db' created successfully!")
                
                # Wait for database to be ready
                await asyncio.sleep(3)
                
                # Verify it's online
                try:
                    status_result = session.run("SHOW DATABASES")
                    for db_record in status_result:
                        if db_record["name"] == "default_db":
                            status = db_record.get('currentStatus', 'unknown')
                            print(f"📊 Database 'default_db' status: {status}")
                            return status == "online"
                except:
                    pass
                
                return True
                        
            except Exception as create_error:
                error_msg = str(create_error).lower()
                if "already exists" in error_msg:
                    print("✅ Database 'default_db' already exists!")
                    return True
                elif i == len(methods):  # Last attempt failed
                    print(f"❌ All attempts failed. Last error: {str(create_error)}")
                    
                    # Try fallback solutions
                    if "illegal" in error_msg and "character" in error_msg:
                        print("💡 Underscore issue detected. Trying workarounds...")
                        return await self._try_workarounds(session)
                    elif "unsupported" in error_msg or "community" in error_msg:
                        print("⚠️  Database creation not supported in Neo4j Community Edition")
                        return self._handle_community_edition(session)
                    else:
                        print("💡 Trying fallback solutions...")
                        return await self._try_workarounds(session)
        
        return False
    
    async def _try_workarounds(self, session):
        """Try workaround solutions for database creation issues"""
        print("🔧 Attempting workaround solutions...")
        
        # Workaround 1: Use the existing 'neo4j' database
        print("   Solution 1: Using existing 'neo4j' database")
        try:
            # Test connection to neo4j database
            test_result = session.run("RETURN 1 as test")
            if test_result.single()["test"] == 1:
                print("✅ Will use 'neo4j' database (Graphiti will adapt)")
                self.using_default_db = True
                
                # Clear any existing data to avoid conflicts
                print("🧹 Clearing existing data from 'neo4j' database...")
                session.run("MATCH (n) DETACH DELETE n")
                print("✅ Database cleared successfully!")
                
                return True
        except Exception as e:
            print(f"   ❌ Failed to use 'neo4j' database: {str(e)}")
        
        # Workaround 2: Create database with different name and inform user
        print("   Solution 2: Creating 'mosdac_db' database")
        try:
            session.run("CREATE DATABASE mosdac_db")
            print("✅ Created 'mosdac_db' database")
            print("⚠️  Note: You may need to configure Graphiti to use 'mosdac_db'")
            return True
        except Exception as e:
            print(f"   ❌ Failed to create 'mosdac_db': {str(e)}")
        
        # Workaround 3: Use community edition approach
        print("   Solution 3: Using Community Edition approach")
        return self._handle_community_edition(session)
    
    def _handle_community_edition(self, session):
        """Handle Neo4j Community Edition limitations"""
        try:
            # Test basic connection with the default database
            test_result = session.run("RETURN 1 as test")
            if test_result.single()["test"] == 1:
                print("✅ Using default database (Community Edition mode)")
                print("💡 Note: Graphiti will use the current database")
                self.using_default_db = True
                
                # Clear any existing data to avoid conflicts
                print("🧹 Clearing existing data from current database...")
                session.run("MATCH (n) DETACH DELETE n")
                print("✅ Database cleared successfully!")
                
                return True
            else:
                return False
        except Exception as test_error:
            print(f"❌ Basic connection test failed: {str(test_error)}")
            return False
    
    async def initialize_graphiti(self):
        """Initialize Graphiti connection and build indices"""
        try:
            print("🔧 Initializing Graphiti connection...")
            
            # First, ensure the database is properly set up
            if not await self.setup_neo4j_database():
                print("❌ Database setup failed!")
                return False
            
            # Try to initialize Graphiti with enhanced error handling
            try:
                print("🔗 Building Graphiti indices and constraints...")
                await self.graphiti.build_indices_and_constraints()
                print("✅ Graphiti initialized successfully!")
                return True
            except Exception as graphiti_error:
                error_msg = str(graphiti_error).lower()
                
                if "database" in error_msg and "default_db" in error_msg:
                    print("⚠️  Graphiti database name issue detected")
                    return await self._handle_graphiti_database_issue(graphiti_error)
                else:
                    raise graphiti_error
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Failed to initialize Graphiti: {error_msg}")
            
            # Provide specific guidance based on error type
            if "default_db" in error_msg:
                print("💡 Database naming issue detected. Possible solutions:")
                print("   1. Use Neo4j Desktop (supports multiple databases)")
                print("   2. Try connecting without specifying database")
                print("   3. Check if Neo4j allows underscore in database names")
            elif "authentication" in error_msg.lower():
                print("💡 Check your Neo4j credentials in the .env file")
            elif "connection" in error_msg.lower():
                print("💡 Ensure Neo4j is running and accessible at localhost:7687")
            
            return False
    
    async def _handle_graphiti_database_issue(self, error):
        """Handle Graphiti-specific database issues"""
        print("🔧 Attempting to resolve Graphiti database issue...")
        
        try:
            # Try to reinitialize with a clean state
            print("   Attempting clean reinitialization...")
            
            # Close and recreate Graphiti instance
            if self.graphiti:
                await self.graphiti.close()
            
            # Wait a moment
            await asyncio.sleep(2)
            
            # Create new Graphiti instance
            self.graphiti = Graphiti(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
            
            # Try again
            await self.graphiti.build_indices_and_constraints()
            print("✅ Graphiti initialized successfully after retry!")
            return True
            
        except Exception as retry_error:
            print(f"❌ Retry failed: {str(retry_error)}")
            print("💡 Manual solutions:")
            print("   1. Create database manually in Neo4j Browser:")
            print("      CREATE DATABASE `default_db`")
            print("   2. Or configure Graphiti to use 'neo4j' database")
            print("   3. Check Neo4j logs for specific error details")
            return False
    
    async def load_satellites(self, satellites_data):
        """Load satellite mission data into knowledge graph"""
        print(f"\n🛰️  Loading {len(satellites_data)} satellites...")
        
        for i, sat in enumerate(satellites_data):
            try:
                print(f"[{i+1}/{len(satellites_data)}] Adding: {sat.get('name', 'Unknown')}")
                
                episode_data = {
                    "type": "satellite_mission",
                    "name": sat.get("name"),
                    "url": sat.get("url"),
                    "description": sat.get("description"),
                    "documents": sat.get("documents", []),
                    "category": "satellite"
                }
                
                await self.graphiti.add_episode(
                    name=f"Satellite Mission: {sat.get('name', 'Unknown')}",
                    episode_body=json.dumps(episode_data, indent=2),
                    source=EpisodeType.json,
                    source_description="MOSDAC Satellite Mission Data",
                    reference_time=self.reference_time,
                )
            except Exception as e:
                print(f"⚠️  Error loading satellite {sat.get('name', 'Unknown')}: {str(e)}")
                continue
    
    async def load_products(self, products_data):
        """Load product catalog data into knowledge graph"""
        print(f"\n📦 Loading {len(products_data)} products...")
        
        for i, product in enumerate(products_data):
            try:
                print(f"[{i+1}/{len(products_data)}] Adding: {product.get('name', 'Unknown Product')}")
                
                episode_data = {
                    "type": "data_product",
                    "name": product.get("name"),
                    "category": product.get("category"),
                    "description": product.get("description"),
                    "url": product.get("url"),
                    "specifications": product.get("specifications", {}),
                    "download_info": product.get("download_info", {}),
                    "related_satellites": product.get("satellites", [])
                }
                
                await self.graphiti.add_episode(
                    name=f"Data Product: {product.get('name', 'Unknown')}",
                    episode_body=json.dumps(episode_data, indent=2),
                    source=EpisodeType.json,
                    source_description="MOSDAC Product Catalog",
                    reference_time=self.reference_time,
                )
            except Exception as e:
                print(f"⚠️  Error loading product {product.get('name', 'Unknown')}: {str(e)}")
                continue
    
    async def load_documents(self, documents_data):
        """Load document metadata into knowledge graph"""
        print(f"\n📄 Loading {len(documents_data)} documents...")
        
        for i, doc in enumerate(documents_data):
            try:
                print(f"[{i+1}/{len(documents_data)}] Adding: {doc.get('title', 'Unknown Document')}")
                
                episode_data = {
                    "type": "documentation",
                    "title": doc.get("title"),
                    "url": doc.get("url"),
                    "file_type": doc.get("file_type"),
                    "size": doc.get("size"),
                    "description": doc.get("description"),
                    "related_mission": doc.get("mission"),
                    "category": "documentation"
                }
                
                await self.graphiti.add_episode(
                    name=f"Document: {doc.get('title', 'Unknown')}",
                    episode_body=json.dumps(episode_data, indent=2),
                    source=EpisodeType.json,
                    source_description="MOSDAC Documentation",
                    reference_time=self.reference_time,
                )
            except Exception as e:
                print(f"⚠️  Error loading document {doc.get('title', 'Unknown')}: {str(e)}")
                continue
    
    async def load_mission_metadata(self, metadata_data):
        """Load mission technical metadata into knowledge graph"""
        print(f"\n🔧 Loading {len(metadata_data)} mission metadata entries...")
        
        for i, meta in enumerate(metadata_data):
            try:
                print(f"[{i+1}/{len(metadata_data)}] Adding metadata for: {meta.get('mission', 'Unknown')}")
                
                episode_data = {
                    "type": "mission_metadata",
                    "mission": meta.get("mission"),
                    "sensors": meta.get("sensors", []),
                    "launch_date": meta.get("launch_date"),
                    "agency": meta.get("agency"),
                    "orbit_type": meta.get("orbit_type"),
                    "applications": meta.get("applications", []),
                    "technical_specs": meta.get("technical_specs", {}),
                    "category": "metadata"
                }
                
                await self.graphiti.add_episode(
                    name=f"Mission Metadata: {meta.get('mission', 'Unknown')}",
                    episode_body=json.dumps(episode_data, indent=2),
                    source=EpisodeType.json,
                    source_description="MOSDAC Mission Technical Metadata",
                    reference_time=self.reference_time,
                )
            except Exception as e:
                print(f"⚠️  Error loading metadata {meta.get('mission', 'Unknown')}: {str(e)}")
                continue
    
    async def load_faqs(self, faqs_data):
        """Load FAQ questions and answers into knowledge graph"""
        print(f"\n❓ Loading {len(faqs_data)} FAQ entries...")
        
        for i, faq in enumerate(faqs_data):
            try:
                print(f"[{i+1}/{len(faqs_data)}] Adding FAQ: {faq.get('question', 'Unknown')[:50]}...")
                
                episode_data = {
                    "type": "faq",
                    "question": faq.get("question"),
                    "answer": faq.get("answer"),
                    "category": faq.get("category", "general"),
                    "tags": faq.get("tags", []),
                    "url": faq.get("url"),
                    "category": "faq"
                }
                
                await self.graphiti.add_episode(
                    name=f"FAQ: {faq.get('question', 'Unknown')[:50]}",
                    episode_body=json.dumps(episode_data, indent=2),
                    source=EpisodeType.json,
                    source_description="MOSDAC FAQ Knowledge Base",
                    reference_time=self.reference_time,
                )
            except Exception as e:
                print(f"⚠️  Error loading FAQ {faq.get('question', 'Unknown')[:50]}: {str(e)}")
                continue
    
    async def load_dataset(self, dataset_name):
        """Load a specific dataset into the knowledge graph"""
        file_path = os.path.join(DATA_DIR, DATASETS[dataset_name])
        
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return False
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            if not data:
                print(f"⚠️  No data found in {dataset_name}")
                return False
            
            # Route to appropriate loader based on dataset type
            if dataset_name == "satellites":
                await self.load_satellites(data)
            elif dataset_name == "products":
                await self.load_products(data)
            elif dataset_name == "documents":
                await self.load_documents(data)
            elif dataset_name == "mission_metadata":
                await self.load_mission_metadata(data)
            elif dataset_name == "faqs":
                await self.load_faqs(data)
            
            return True
            
        except Exception as e:
            print(f"❌ Error loading {dataset_name}: {str(e)}")
            return False
    
    async def load_all_datasets(self):
        """Load all available datasets into the knowledge graph"""
        print("🚀 Starting MOSDAC Knowledge Graph Loading...")
        
        # Initialize Graphiti first
        if not await self.initialize_graphiti():
            print("❌ Failed to initialize Graphiti. Exiting...")
            return
        
        total_loaded = 0
        
        for dataset_name in DATASETS.keys():
            print(f"\n{'='*50}")
            print(f"Loading {dataset_name.upper()} dataset...")
            
            success = await self.load_dataset(dataset_name)
            if success:
                total_loaded += 1
                print(f"✅ {dataset_name} loaded successfully!")
            else:
                print(f"❌ Failed to load {dataset_name}")
        
        print(f"\n{'='*50}")
        print(f"🎉 Knowledge Graph Loading Complete!")
        print(f"📊 Successfully loaded {total_loaded}/{len(DATASETS)} datasets")
        
        # Display some statistics
        await self.display_stats()
    
    async def display_stats(self):
        """Display knowledge graph statistics"""
        try:
            with self.driver.session() as session:
                # Count nodes
                node_result = session.run("MATCH (n) RETURN count(n) as node_count")
                node_count = node_result.single()["node_count"]
                
                # Count relationships
                rel_result = session.run("MATCH ()-[r]-() RETURN count(r) as rel_count")
                rel_count = rel_result.single()["rel_count"]
                
                print(f"📊 Knowledge Graph Statistics:")
                print(f"   • Nodes: {node_count}")
                print(f"   • Relationships: {rel_count}")
                
        except Exception as e:
            print(f"⚠️  Could not retrieve statistics: {str(e)}")
    
    async def close(self):
        """Close all connections"""
        try:
            if self.graphiti:
                await self.graphiti.close()
            if self.driver:
                self.driver.close()
            print("✅ All connections closed successfully!")
        except Exception as e:
            print(f"⚠️  Error closing connections: {str(e)}")

async def main():
    """Main execution function"""
    loader = MOSDACGraphLoader()
    
    try:
        # Load all datasets
        await loader.load_all_datasets()
    except KeyboardInterrupt:
        print("\n🛑 Process interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # Ensure connections are closed
        await loader.close()

if __name__ == "__main__":
    asyncio.run(main())