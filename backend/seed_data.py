"""
Seed SQLite with static datasets.
Falls back to hardcoded data if CSV files are missing.
"""
import asyncio
import logging
import os
import csv

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

# ── Hardcoded fallback data ──────────────────────────────────────────────────

SEED_AIRPORTS = [
    {"name": "Indira Gandhi International Airport", "city": "New Delhi", "iata_code": "DEL",
     "state": "Delhi", "latitude": 28.5562, "longitude": 77.1000, "is_operational": True},
    {"name": "Chhatrapati Shivaji Maharaj International Airport", "city": "Mumbai", "iata_code": "BOM",
     "state": "Maharashtra", "latitude": 19.0896, "longitude": 72.8656, "is_operational": True},
    {"name": "Kempegowda International Airport", "city": "Bengaluru", "iata_code": "BLR",
     "state": "Karnataka", "latitude": 13.1986, "longitude": 77.7066, "is_operational": True},
    {"name": "Chennai International Airport", "city": "Chennai", "iata_code": "MAA",
     "state": "Tamil Nadu", "latitude": 12.9900, "longitude": 80.1693, "is_operational": True},
    {"name": "Rajiv Gandhi International Airport", "city": "Hyderabad", "iata_code": "HYD",
     "state": "Telangana", "latitude": 17.2313, "longitude": 78.4298, "is_operational": True},
    {"name": "Pune Airport", "city": "Pune", "iata_code": "PNQ",
     "state": "Maharashtra", "latitude": 18.5822, "longitude": 73.9197, "is_operational": True},
    {"name": "Sardar Vallabhbhai Patel International Airport", "city": "Ahmedabad", "iata_code": "AMD",
     "state": "Gujarat", "latitude": 23.0772, "longitude": 72.6347, "is_operational": True},
    {"name": "Jaipur International Airport", "city": "Jaipur", "iata_code": "JAI",
     "state": "Rajasthan", "latitude": 26.8242, "longitude": 75.8122, "is_operational": True},
    {"name": "Lokpriya Gopinath Bordoloi International Airport", "city": "Guwahati", "iata_code": "GAU",
     "state": "Assam", "latitude": 26.1061, "longitude": 91.5859, "is_operational": True},
    {"name": "Netaji Subhas Chandra Bose International Airport", "city": "Kolkata", "iata_code": "CCU",
     "state": "West Bengal", "latitude": 22.6520, "longitude": 88.4463, "is_operational": True},
    {"name": "Cochin International Airport", "city": "Kochi", "iata_code": "COK",
     "state": "Kerala", "latitude": 10.1520, "longitude": 76.4019, "is_operational": True},
    {"name": "Bhopal Airport", "city": "Bhopal", "iata_code": "BHO",
     "state": "Madhya Pradesh", "latitude": 23.2875, "longitude": 77.3374, "is_operational": True},
    {"name": "Lucknow Airport", "city": "Lucknow", "iata_code": "LKO",
     "state": "Uttar Pradesh", "latitude": 26.7606, "longitude": 80.8893, "is_operational": True},
    {"name": "Chandigarh Airport", "city": "Chandigarh", "iata_code": "IXC",
     "state": "Chandigarh", "latitude": 30.6735, "longitude": 76.7885, "is_operational": True},
    {"name": "Surat Airport", "city": "Surat", "iata_code": "STV",
     "state": "Gujarat", "latitude": 21.1141, "longitude": 72.7418, "is_operational": True},
    {"name": "Nagpur Airport", "city": "Nagpur", "iata_code": "NAG",
     "state": "Maharashtra", "latitude": 21.0922, "longitude": 79.0472, "is_operational": True},
    {"name": "Coimbatore International Airport", "city": "Coimbatore", "iata_code": "CJB",
     "state": "Tamil Nadu", "latitude": 11.0300, "longitude": 77.0434, "is_operational": True},
    {"name": "Trivandrum International Airport", "city": "Thiruvananthapuram", "iata_code": "TRV",
     "state": "Kerala", "latitude": 8.4821, "longitude": 76.9201, "is_operational": True},
    {"name": "Varanasi Airport", "city": "Varanasi", "iata_code": "VNS",
     "state": "Uttar Pradesh", "latitude": 25.4524, "longitude": 82.8593, "is_operational": True},
    {"name": "Patna Airport", "city": "Patna", "iata_code": "PAT",
     "state": "Bihar", "latitude": 25.5913, "longitude": 85.0877, "is_operational": True},
]

SEED_RAILWAY = [
    {"station_name": "New Delhi", "station_code": "NDLS", "state": "Delhi", "latitude": 28.6408, "longitude": 77.2219},
    {"station_name": "Mumbai CST", "station_code": "CSTM", "state": "Maharashtra", "latitude": 18.9398, "longitude": 72.8355},
    {"station_name": "Mumbai Central", "station_code": "BCT", "state": "Maharashtra", "latitude": 18.9690, "longitude": 72.8197},
    {"station_name": "Pune Junction", "station_code": "PUNE", "state": "Maharashtra", "latitude": 18.5283, "longitude": 73.8741},
    {"station_name": "Bengaluru City Junction", "station_code": "SBC", "state": "Karnataka", "latitude": 12.9772, "longitude": 77.5730},
    {"station_name": "Chennai Central", "station_code": "MAS", "state": "Tamil Nadu", "latitude": 13.0827, "longitude": 80.2707},
    {"station_name": "Howrah Junction", "station_code": "HWH", "state": "West Bengal", "latitude": 22.5851, "longitude": 88.3426},
    {"station_name": "Secunderabad Junction", "station_code": "SC", "state": "Telangana", "latitude": 17.4344, "longitude": 78.5013},
    {"station_name": "Ahmedabad Junction", "station_code": "ADI", "state": "Gujarat", "latitude": 23.0258, "longitude": 72.6020},
    {"station_name": "Jaipur Junction", "station_code": "JP", "state": "Rajasthan", "latitude": 26.9193, "longitude": 75.7876},
    {"station_name": "Lucknow Junction", "station_code": "LKO", "state": "Uttar Pradesh", "latitude": 26.8322, "longitude": 80.9199},
    {"station_name": "Kanpur Central", "station_code": "CNB", "state": "Uttar Pradesh", "latitude": 26.4409, "longitude": 80.3465},
    {"station_name": "Nagpur Junction", "station_code": "NGP", "state": "Maharashtra", "latitude": 21.1498, "longitude": 79.0861},
    {"station_name": "Patna Junction", "station_code": "PNBE", "state": "Bihar", "latitude": 25.6099, "longitude": 85.1246},
    {"station_name": "Bhopal Junction", "station_code": "BPL", "state": "Madhya Pradesh", "latitude": 23.2615, "longitude": 77.4126},
    {"station_name": "Indore Junction", "station_code": "INDB", "state": "Madhya Pradesh", "latitude": 22.7244, "longitude": 75.8839},
    {"station_name": "Surat Junction", "station_code": "ST", "state": "Gujarat", "latitude": 21.2014, "longitude": 72.8371},
    {"station_name": "Vadodara Junction", "station_code": "BRC", "state": "Gujarat", "latitude": 22.3143, "longitude": 73.1844},
    {"station_name": "Coimbatore Junction", "station_code": "CBE", "state": "Tamil Nadu", "latitude": 11.0015, "longitude": 76.9666},
    {"station_name": "Kochi Ernakulam Junction", "station_code": "ERS", "state": "Kerala", "latitude": 9.9849, "longitude": 76.2873},
    {"station_name": "Thiruvananthapuram Central", "station_code": "TVC", "state": "Kerala", "latitude": 8.4875, "longitude": 76.9525},
    {"station_name": "Visakhapatnam Junction", "station_code": "VSKP", "state": "Andhra Pradesh", "latitude": 17.6868, "longitude": 83.2185},
    {"station_name": "Vijayawada Junction", "station_code": "BZA", "state": "Andhra Pradesh", "latitude": 16.5193, "longitude": 80.6305},
    {"station_name": "Guwahati Railway Station", "station_code": "GHY", "state": "Assam", "latitude": 26.1858, "longitude": 91.7386},
    {"station_name": "Chandigarh Junction", "station_code": "CDG", "state": "Chandigarh", "latitude": 30.7088, "longitude": 76.7987},
    {"station_name": "Varanasi Junction", "station_code": "BSB", "state": "Uttar Pradesh", "latitude": 25.3124, "longitude": 82.9997},
    {"station_name": "Allahabad Junction", "station_code": "ALD", "state": "Uttar Pradesh", "latitude": 25.4381, "longitude": 81.8789},
    {"station_name": "Agra Cantt", "station_code": "AGC", "state": "Uttar Pradesh", "latitude": 27.1592, "longitude": 77.9714},
    {"station_name": "Amritsar Junction", "station_code": "ASR", "state": "Punjab", "latitude": 31.6340, "longitude": 74.8723},
    {"station_name": "Ludhiana Junction", "station_code": "LDH", "state": "Punjab", "latitude": 30.9011, "longitude": 75.8573},
    {"station_name": "Rajkot Junction", "station_code": "RJT", "state": "Gujarat", "latitude": 22.3072, "longitude": 70.8017},
    {"station_name": "Nashik Road", "station_code": "NK", "state": "Maharashtra", "latitude": 19.9975, "longitude": 73.7898},
    {"station_name": "Aurangabad Junction", "station_code": "AWB", "state": "Maharashtra", "latitude": 19.8762, "longitude": 75.3433},
    {"station_name": "Madurai Junction", "station_code": "MDU", "state": "Tamil Nadu", "latitude": 9.9252, "longitude": 78.1198},
    {"station_name": "Tiruchirappalli Junction", "station_code": "TPJ", "state": "Tamil Nadu", "latitude": 10.8156, "longitude": 78.6912},
    {"station_name": "Bhubaneswar Railway Station", "station_code": "BBS", "state": "Odisha", "latitude": 20.2625, "longitude": 85.8391},
    {"station_name": "Raipur Junction", "station_code": "R", "state": "Chhattisgarh", "latitude": 21.2449, "longitude": 81.6296},
    {"station_name": "Ranchi Junction", "station_code": "RNC", "state": "Jharkhand", "latitude": 23.3441, "longitude": 85.3096},
    {"station_name": "Dehradun Railway Station", "station_code": "DDN", "state": "Uttarakhand", "latitude": 30.3255, "longitude": 78.0337},
    {"station_name": "Jammu Tawi", "station_code": "JAT", "state": "Jammu & Kashmir", "latitude": 32.7266, "longitude": 74.8570},
    {"station_name": "Mysuru Junction", "station_code": "MYS", "state": "Karnataka", "latitude": 12.3052, "longitude": 76.6551},
    {"station_name": "Hubballi Junction", "station_code": "UBL", "state": "Karnataka", "latitude": 15.3647, "longitude": 75.1239},
    {"station_name": "Mangaluru Central", "station_code": "MAQ", "state": "Karnataka", "latitude": 12.8701, "longitude": 74.8425},
    {"station_name": "Kozhikode Railway Station", "station_code": "CLT", "state": "Kerala", "latitude": 11.2509, "longitude": 75.7803},
    {"station_name": "Salem Junction", "station_code": "SA", "state": "Tamil Nadu", "latitude": 11.6455, "longitude": 78.1453},
    {"station_name": "Kolhapur CSMT", "station_code": "KOP", "state": "Maharashtra", "latitude": 16.6988, "longitude": 74.2127},
    {"station_name": "Solapur Junction", "station_code": "SUR", "state": "Maharashtra", "latitude": 17.6760, "longitude": 75.9099},
    {"station_name": "Jabalpur Junction", "station_code": "JBP", "state": "Madhya Pradesh", "latitude": 23.1815, "longitude": 79.9864},
    {"station_name": "Gwalior Junction", "station_code": "GWL", "state": "Madhya Pradesh", "latitude": 26.2209, "longitude": 78.1665},
    {"station_name": "Jodhpur Junction", "station_code": "JU", "state": "Rajasthan", "latitude": 26.2925, "longitude": 73.0358},
]

SEED_CENSUS = [
    {"state": "Maharashtra", "district": "Pune", "total_population": 9429408, "urban_population": 7761886, "rural_population": 1667522, "literacy_rate": 86.15, "sex_ratio": 915, "workers_total": 3986000},
    {"state": "Maharashtra", "district": "Mumbai", "total_population": 12442373, "urban_population": 12442373, "rural_population": 0, "literacy_rate": 89.73, "sex_ratio": 838, "workers_total": 5000000},
    {"state": "Maharashtra", "district": "Nagpur", "total_population": 4653570, "urban_population": 2873477, "rural_population": 1780093, "literacy_rate": 85.52, "sex_ratio": 951, "workers_total": 1750000},
    {"state": "Karnataka", "district": "Bengaluru Urban", "total_population": 9621551, "urban_population": 8499399, "rural_population": 1122152, "literacy_rate": 88.48, "sex_ratio": 916, "workers_total": 4200000},
    {"state": "Tamil Nadu", "district": "Chennai", "total_population": 7088000, "urban_population": 7088000, "rural_population": 0, "literacy_rate": 90.18, "sex_ratio": 989, "workers_total": 3100000},
    {"state": "Delhi", "district": "New Delhi", "total_population": 11034555, "urban_population": 11034555, "rural_population": 0, "literacy_rate": 86.34, "sex_ratio": 866, "workers_total": 4300000},
    {"state": "West Bengal", "district": "Kolkata", "total_population": 4496694, "urban_population": 4496694, "rural_population": 0, "literacy_rate": 87.14, "sex_ratio": 899, "workers_total": 1800000},
    {"state": "Telangana", "district": "Hyderabad", "total_population": 3943323, "urban_population": 3943323, "rural_population": 0, "literacy_rate": 83.25, "sex_ratio": 945, "workers_total": 1600000},
    {"state": "Gujarat", "district": "Ahmedabad", "total_population": 7208200, "urban_population": 6352254, "rural_population": 855946, "literacy_rate": 86.65, "sex_ratio": 897, "workers_total": 3000000},
    {"state": "Rajasthan", "district": "Jaipur", "total_population": 6626178, "urban_population": 3073350, "rural_population": 3552828, "literacy_rate": 75.51, "sex_ratio": 898, "workers_total": 2100000},
    {"state": "Uttar Pradesh", "district": "Lucknow", "total_population": 4589838, "urban_population": 2901474, "rural_population": 1688364, "literacy_rate": 77.29, "sex_ratio": 917, "workers_total": 1600000},
    {"state": "Madhya Pradesh", "district": "Bhopal", "total_population": 2368145, "urban_population": 1795648, "rural_population": 572497, "literacy_rate": 82.25, "sex_ratio": 915, "workers_total": 900000},
    {"state": "Kerala", "district": "Ernakulam", "total_population": 3282388, "urban_population": 1688556, "rural_population": 1593832, "literacy_rate": 95.89, "sex_ratio": 1027, "workers_total": 1200000},
    {"state": "Punjab", "district": "Ludhiana", "total_population": 3498739, "urban_population": 1618674, "rural_population": 1880065, "literacy_rate": 82.20, "sex_ratio": 873, "workers_total": 1400000},
    {"state": "Bihar", "district": "Patna", "total_population": 5838465, "urban_population": 2049156, "rural_population": 3789309, "literacy_rate": 70.68, "sex_ratio": 897, "workers_total": 2000000},
    {"state": "Andhra Pradesh", "district": "Visakhapatnam", "total_population": 4290589, "urban_population": 1728128, "rural_population": 2562461, "literacy_rate": 67.97, "sex_ratio": 1006, "workers_total": 1600000},
    {"state": "Odisha", "district": "Khorda", "total_population": 2251673, "urban_population": 1025048, "rural_population": 1226625, "literacy_rate": 85.96, "sex_ratio": 940, "workers_total": 850000},
    {"state": "Chhattisgarh", "district": "Raipur", "total_population": 1010087, "urban_population": 755975, "rural_population": 254112, "literacy_rate": 83.57, "sex_ratio": 948, "workers_total": 380000},
    {"state": "Jharkhand", "district": "Ranchi", "total_population": 2914253, "urban_population": 1073440, "rural_population": 1840813, "literacy_rate": 76.06, "sex_ratio": 947, "workers_total": 1000000},
    {"state": "Assam", "district": "Kamrup Metropolitan", "total_population": 1253938, "urban_population": 963429, "rural_population": 290509, "literacy_rate": 88.35, "sex_ratio": 937, "workers_total": 450000},
]

SEED_CRIME = [
    {"year": 2022, "state": "Maharashtra", "district": "Pune", "total_ipc_crimes": 48000, "crimes_per_lakh": 195.0, "property_crimes": 15000, "economic_offences": 5000},
    {"year": 2021, "state": "Maharashtra", "district": "Pune", "total_ipc_crimes": 45000, "crimes_per_lakh": 185.0, "property_crimes": 14000, "economic_offences": 4500},
    {"year": 2020, "state": "Maharashtra", "district": "Pune", "total_ipc_crimes": 42000, "crimes_per_lakh": 175.0, "property_crimes": 13000, "economic_offences": 4000},
    {"year": 2022, "state": "Karnataka", "district": "Bengaluru Urban", "total_ipc_crimes": 62000, "crimes_per_lakh": 210.0, "property_crimes": 20000, "economic_offences": 7000},
    {"year": 2021, "state": "Karnataka", "district": "Bengaluru Urban", "total_ipc_crimes": 58000, "crimes_per_lakh": 198.0, "property_crimes": 18500, "economic_offences": 6500},
    {"year": 2022, "state": "Tamil Nadu", "district": "Chennai", "total_ipc_crimes": 78000, "crimes_per_lakh": 225.0, "property_crimes": 25000, "economic_offences": 8000},
    {"year": 2022, "state": "Delhi", "district": "New Delhi", "total_ipc_crimes": 210000, "crimes_per_lakh": 975.0, "property_crimes": 60000, "economic_offences": 15000},
    {"year": 2021, "state": "Delhi", "district": "New Delhi", "total_ipc_crimes": 195000, "crimes_per_lakh": 900.0, "property_crimes": 55000, "economic_offences": 14000},
    {"year": 2022, "state": "West Bengal", "district": "Kolkata", "total_ipc_crimes": 45000, "crimes_per_lakh": 250.0, "property_crimes": 14000, "economic_offences": 4000},
    {"year": 2022, "state": "Telangana", "district": "Hyderabad", "total_ipc_crimes": 52000, "crimes_per_lakh": 215.0, "property_crimes": 16000, "economic_offences": 5500},
    {"year": 2022, "state": "Gujarat", "district": "Ahmedabad", "total_ipc_crimes": 55000, "crimes_per_lakh": 195.0, "property_crimes": 18000, "economic_offences": 5000},
    {"year": 2022, "state": "Rajasthan", "district": "Jaipur", "total_ipc_crimes": 42000, "crimes_per_lakh": 185.0, "property_crimes": 13000, "economic_offences": 4000},
    {"year": 2022, "state": "Uttar Pradesh", "district": "Lucknow", "total_ipc_crimes": 48000, "crimes_per_lakh": 220.0, "property_crimes": 15000, "economic_offences": 4500},
    {"year": 2022, "state": "Madhya Pradesh", "district": "Bhopal", "total_ipc_crimes": 35000, "crimes_per_lakh": 280.0, "property_crimes": 11000, "economic_offences": 3500},
    {"year": 2022, "state": "Kerala", "district": "Ernakulam", "total_ipc_crimes": 22000, "crimes_per_lakh": 160.0, "property_crimes": 7000, "economic_offences": 2500},
    {"year": 2022, "state": "Bihar", "district": "Patna", "total_ipc_crimes": 38000, "crimes_per_lakh": 310.0, "property_crimes": 12000, "economic_offences": 3000},
]

SEED_MSME = [
    {"state": "Maharashtra", "district": "Pune", "nic_code": "62", "sector_name": "IT & Software", "enterprise_count": 15200, "micro_count": 12000, "small_count": 2800},
    {"state": "Maharashtra", "district": "Pune", "nic_code": "45", "sector_name": "Motor Vehicle Trade", "enterprise_count": 8500, "micro_count": 7000, "small_count": 1300},
    {"state": "Maharashtra", "district": "Pune", "nic_code": "56", "sector_name": "Food & Beverage Services", "enterprise_count": 22000, "micro_count": 20000, "small_count": 1800},
    {"state": "Maharashtra", "district": "Pune", "nic_code": "47", "sector_name": "Retail Trade", "enterprise_count": 35000, "micro_count": 33000, "small_count": 1800},
    {"state": "Maharashtra", "district": "Pune", "nic_code": "25", "sector_name": "Fabricated Metal Products", "enterprise_count": 6800, "micro_count": 5500, "small_count": 1100},
    {"state": "Karnataka", "district": "Bengaluru Urban", "nic_code": "62", "sector_name": "IT & Software", "enterprise_count": 42000, "micro_count": 30000, "small_count": 10000},
    {"state": "Karnataka", "district": "Bengaluru Urban", "nic_code": "47", "sector_name": "Retail Trade", "enterprise_count": 55000, "micro_count": 50000, "small_count": 4500},
    {"state": "Karnataka", "district": "Bengaluru Urban", "nic_code": "56", "sector_name": "Food & Beverage Services", "enterprise_count": 38000, "micro_count": 35000, "small_count": 2800},
    {"state": "Tamil Nadu", "district": "Chennai", "nic_code": "47", "sector_name": "Retail Trade", "enterprise_count": 48000, "micro_count": 44000, "small_count": 3800},
    {"state": "Tamil Nadu", "district": "Chennai", "nic_code": "62", "sector_name": "IT & Software", "enterprise_count": 18000, "micro_count": 13000, "small_count": 4500},
    {"state": "Delhi", "district": "New Delhi", "nic_code": "47", "sector_name": "Retail Trade", "enterprise_count": 120000, "micro_count": 112000, "small_count": 7500},
    {"state": "Delhi", "district": "New Delhi", "nic_code": "56", "sector_name": "Food & Beverage Services", "enterprise_count": 65000, "micro_count": 60000, "small_count": 4500},
    {"state": "Delhi", "district": "New Delhi", "nic_code": "46", "sector_name": "Wholesale Trade", "enterprise_count": 45000, "micro_count": 40000, "small_count": 4500},
    {"state": "Gujarat", "district": "Ahmedabad", "nic_code": "14", "sector_name": "Wearing Apparel", "enterprise_count": 28000, "micro_count": 25000, "small_count": 2800},
    {"state": "Gujarat", "district": "Ahmedabad", "nic_code": "47", "sector_name": "Retail Trade", "enterprise_count": 42000, "micro_count": 39000, "small_count": 2800},
    {"state": "Rajasthan", "district": "Jaipur", "nic_code": "14", "sector_name": "Wearing Apparel & Gems", "enterprise_count": 22000, "micro_count": 20000, "small_count": 1800},
    {"state": "Rajasthan", "district": "Jaipur", "nic_code": "47", "sector_name": "Retail Trade", "enterprise_count": 32000, "micro_count": 30000, "small_count": 1900},
    {"state": "Uttar Pradesh", "district": "Lucknow", "nic_code": "47", "sector_name": "Retail Trade", "enterprise_count": 45000, "micro_count": 42000, "small_count": 2800},
    {"state": "Kerala", "district": "Ernakulam", "nic_code": "47", "sector_name": "Retail Trade", "enterprise_count": 28000, "micro_count": 26000, "small_count": 1800},
    {"state": "West Bengal", "district": "Kolkata", "nic_code": "47", "sector_name": "Retail Trade", "enterprise_count": 85000, "micro_count": 80000, "small_count": 4500},
]


async def seed_if_empty():
    """Load seed data into SQLite tables only if they are empty."""
    from database import AsyncSessionLocal
    from models import Airport, RailwayStation, CensusData, CrimeData, MsmeData
    from sqlalchemy import select, func

    async with AsyncSessionLocal() as db:
        # Check airports
        count = (await db.execute(select(func.count()).select_from(Airport))).scalar()
        if count == 0:
            logger.info("Seeding airports...")
            for a in SEED_AIRPORTS:
                db.add(Airport(**a))
            await db.commit()
            logger.info(f"Seeded {len(SEED_AIRPORTS)} airports")

        # Check railway stations
        count = (await db.execute(select(func.count()).select_from(RailwayStation))).scalar()
        if count == 0:
            logger.info("Seeding railway stations...")
            # Try CSV first
            csv_path = os.path.join(DATA_DIR, "railway_stations.csv")
            loaded = False
            if os.path.exists(csv_path):
                try:
                    with open(csv_path, encoding="utf-8") as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            try:
                                db.add(RailwayStation(
                                    station_name=row.get("station_name") or row.get("Station_Name") or row.get("name", ""),
                                    station_code=row.get("station_code") or row.get("Station_Code") or row.get("code"),
                                    state=row.get("state") or row.get("State"),
                                    latitude=float(row.get("latitude") or row.get("lat") or 0) or None,
                                    longitude=float(row.get("longitude") or row.get("lon") or 0) or None,
                                ))
                            except (ValueError, TypeError):
                                continue
                    await db.commit()
                    loaded = True
                    logger.info("Loaded railway stations from CSV")
                except Exception as e:
                    logger.warning(f"CSV load failed: {e}")

            if not loaded:
                for s in SEED_RAILWAY:
                    db.add(RailwayStation(**s))
                await db.commit()
                logger.info(f"Seeded {len(SEED_RAILWAY)} railway stations from fallback")

        # Census data
        count = (await db.execute(select(func.count()).select_from(CensusData))).scalar()
        if count == 0:
            logger.info("Seeding census data...")
            csv_path = os.path.join(DATA_DIR, "census_district.csv")
            loaded = False
            if os.path.exists(csv_path):
                try:
                    with open(csv_path, encoding="utf-8") as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            try:
                                db.add(CensusData(
                                    district_code=row.get("district_code"),
                                    state=row.get("state", ""),
                                    district=row.get("district", ""),
                                    total_population=int(row.get("total_population") or 0) or None,
                                    urban_population=int(row.get("urban_population") or 0) or None,
                                    rural_population=int(row.get("rural_population") or 0) or None,
                                    literacy_rate=float(row.get("literacy_rate") or 0) or None,
                                    sex_ratio=int(row.get("sex_ratio") or 0) or None,
                                    workers_total=int(row.get("workers_total") or 0) or None,
                                ))
                            except (ValueError, TypeError):
                                continue
                    await db.commit()
                    loaded = True
                except Exception as e:
                    logger.warning(f"Census CSV load failed: {e}")

            if not loaded:
                for c in SEED_CENSUS:
                    db.add(CensusData(**c))
                await db.commit()
                logger.info(f"Seeded {len(SEED_CENSUS)} census records from fallback")

        # Crime data
        count = (await db.execute(select(func.count()).select_from(CrimeData))).scalar()
        if count == 0:
            logger.info("Seeding crime data...")
            csv_path = os.path.join(DATA_DIR, "ncrb_crime.csv")
            loaded = False
            if os.path.exists(csv_path):
                try:
                    with open(csv_path, encoding="utf-8") as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            try:
                                db.add(CrimeData(
                                    year=int(row.get("year", 2022)),
                                    state=row.get("state", ""),
                                    district=row.get("district") or row.get("city_district", ""),
                                    total_ipc_crimes=int(row.get("total_ipc_crimes") or 0) or None,
                                    crimes_per_lakh=float(row.get("crimes_per_lakh") or 0) or None,
                                    property_crimes=int(row.get("property_crimes") or 0) or None,
                                    economic_offences=int(row.get("economic_offences") or 0) or None,
                                ))
                            except (ValueError, TypeError):
                                continue
                    await db.commit()
                    loaded = True
                except Exception as e:
                    logger.warning(f"Crime CSV load failed: {e}")

            if not loaded:
                for c in SEED_CRIME:
                    db.add(CrimeData(**c))
                await db.commit()
                logger.info(f"Seeded {len(SEED_CRIME)} crime records from fallback")

        # MSME data
        count = (await db.execute(select(func.count()).select_from(MsmeData))).scalar()
        if count == 0:
            logger.info("Seeding MSME data...")
            csv_path = os.path.join(DATA_DIR, "msme_district.csv")
            loaded = False
            if os.path.exists(csv_path):
                try:
                    with open(csv_path, encoding="utf-8") as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            try:
                                db.add(MsmeData(
                                    state=row.get("state", ""),
                                    district=row.get("district", ""),
                                    nic_code=row.get("nic_code") or row.get("nic_2digit_code"),
                                    sector_name=row.get("sector_name") or row.get("nic_description"),
                                    enterprise_count=int(row.get("enterprise_count") or 0) or None,
                                    micro_count=int(row.get("micro_count") or 0) or None,
                                    small_count=int(row.get("small_count") or 0) or None,
                                ))
                            except (ValueError, TypeError):
                                continue
                    await db.commit()
                    loaded = True
                except Exception as e:
                    logger.warning(f"MSME CSV load failed: {e}")

            if not loaded:
                for m in SEED_MSME:
                    db.add(MsmeData(**m))
                await db.commit()
                logger.info(f"Seeded {len(SEED_MSME)} MSME records from fallback")

    logger.info("Database seeding complete")


if __name__ == "__main__":
    asyncio.run(seed_if_empty())
