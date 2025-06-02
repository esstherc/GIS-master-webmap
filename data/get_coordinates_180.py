import requests
import csv
import pandas as pd
import time
import chardet

def detect_file_encoding(file_path):
    """
    Detect the encoding of a file
    """
    try:
        with open(file_path, 'rb') as file:
            raw_data = file.read()
            result = chardet.detect(raw_data)
            encoding = result['encoding']
            confidence = result['confidence']
            print(f"📄 Detected file encoding: {encoding} (confidence: {confidence:.2f})")
            return encoding
    except Exception as e:
        print(f"❌ Error detecting encoding: {e}")
        return None

def read_csv_with_encoding(file_path):
    """
    Try to read CSV with different encodings
    """
    # List of common encodings to try
    encodings_to_try = ['utf-8', 'utf-8-sig', 'latin-1', 'iso-8859-1', 'cp1252', 'windows-1252']
    
    # First try to detect encoding
    detected_encoding = detect_file_encoding(file_path)
    if detected_encoding:
        encodings_to_try.insert(0, detected_encoding)
    
    for encoding in encodings_to_try:
        try:
            print(f"🔄 Trying to read with encoding: {encoding}")
            df = pd.read_csv(file_path, encoding=encoding)
            print(f"✅ Successfully read file with encoding: {encoding}")
            return df, encoding
        except UnicodeDecodeError:
            print(f"❌ Failed with encoding: {encoding}")
            continue
        except Exception as e:
            print(f"❌ Error with encoding {encoding}: {e}")
            continue
    
    raise Exception("Could not read the file with any common encoding")

def get_all_university_coordinates():
    """
    Get coordinates for all universities in the CSV file
    """
    # Read the CSV file to get all unique universities
    try:
        df, file_encoding = read_csv_with_encoding('unique-uni/all_msgis_institutions.csv')
        print(f"📁 File successfully loaded with {file_encoding} encoding")
    except Exception as e:
        print(f"❌ Error reading CSV file: {e}")
        return []
    
    universities = df['Institution'].unique().tolist()

    print(f"Found {len(universities)} unique universities")

    # Your OpenCage API key
    api_key = '18c9586b4d8940878bcd8018a0c93e59'

    # Base URL for OpenCage Geocoding API
    base_url = 'https://api.opencagedata.com/geocode/v1/json'

    # List to hold the university data
    university_data = []

    # Iterate over each university to get its coordinates
    for i, university in enumerate(universities):
        print(f"Processing {i+1}/{len(universities)}: {university}")
        
        # Define the parameters for the API request
        params = {
            'q': f"{university} United States",  # Add "United States" for better accuracy
            'key': api_key,
            'limit': 1,
            'countrycode': 'us'  # Restrict to US only
        }
        
        try:
            # Send the request to the OpenCage Geocoding API
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            
            # Parse the JSON response
            data = response.json()
            
            # Extract latitude and longitude
            if data['results']:
                result = data['results'][0]
                latitude = result['geometry']['lat']
                longitude = result['geometry']['lng']
                formatted_address = result['formatted']
                confidence = result.get('confidence', 0)
                
                # Try to extract state from components
                state = None
                city = None
                if 'components' in result:
                    components = result['components']
                    state = components.get('state_code') or components.get('state')
                    city = components.get('city') or components.get('town') or components.get('village')
                
                university_data.append([
                    university, 
                    latitude, 
                    longitude, 
                    formatted_address, 
                    state, 
                    city,
                    confidence
                ])
                print(f"  ✓ Found: {latitude}, {longitude} (confidence: {confidence})")
            else:
                university_data.append([university, None, None, 'Not found', None, None, 0])
                print(f"  ✗ Not found")
                
        except requests.exceptions.RequestException as e:
            print(f"  ✗ Request Error: {e}")
            university_data.append([university, None, None, f'Request Error: {e}', None, None, 0])
        except Exception as e:
            print(f"  ✗ Error: {e}")
            university_data.append([university, None, None, f'Error: {e}', None, None, 0])
        
        # Add delay to respect API rate limits (OpenCage allows 1 request per second for free tier)
        time.sleep(1.1)

    return university_data

def save_coordinates_to_csv(university_data, filename='universities_coordinates_all.csv'):
    """
    Save university coordinates to CSV file
    """
    # Write the data to a CSV file
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['University', 'Latitude', 'Longitude', 'Address', 'State', 'City', 'Confidence'])
        writer.writerows(university_data)

    print(f"\nCSV file '{filename}' has been created with {len(university_data)} universities.")

def print_summary(university_data):
    """
    Print summary statistics
    """
    # Print summary
    found = sum(1 for row in university_data if row[1] is not None)
    not_found = len(university_data) - found
    
    print(f"\n" + "="*50)
    print(f"GEOCODING SUMMARY")
    print(f"="*50)
    print(f"Total universities processed: {len(university_data)}")
    print(f"Successfully geocoded: {found}")
    print(f"Not found: {not_found}")
    print(f"Success rate: {found/len(university_data)*100:.1f}%")
    
    # Print universities that were not found
    if not_found > 0:
        print(f"\n❌ Universities not found:")
        for row in university_data:
            if row[1] is None:
                print(f"  - {row[0]}")
    
    # Print confidence statistics for found universities
    found_data = [row for row in university_data if row[1] is not None]
    if found_data:
        confidences = [row[6] for row in found_data]
        avg_confidence = sum(confidences) / len(confidences)
        print(f"\n📊 Confidence Statistics:")
        print(f"Average confidence: {avg_confidence:.1f}")
        print(f"High confidence (>7): {sum(1 for c in confidences if c > 7)}")
        print(f"Medium confidence (4-7): {sum(1 for c in confidences if 4 <= c <= 7)}")
        print(f"Low confidence (<4): {sum(1 for c in confidences if c < 4)}")

def verify_data_integrity():
    """
    Verify the original CSV file structure
    """
    try:
        df, encoding = read_csv_with_encoding('unique-uni/all_msgis_institutions.csv')
        print(f"📁 Original CSV file loaded successfully with {encoding} encoding")
        print(f"   Total rows: {len(df)}")
        print(f"   Unique institutions: {df['Institution'].nunique()}")
        print(f"   Columns: {list(df.columns)}")
        
        # Display first few institutions to verify
        print(f"\n📋 First 5 institutions:")
        for i, institution in enumerate(df['Institution'].unique()[:5]):
            print(f"   {i+1}. {institution}")
        
        return True
    except FileNotFoundError:
        print(f"❌ Error: Could not find 'unique-uni/all_msgis_institutions.csv'")
        print(f"   Please make sure the file exists in the correct location.")
        return False
    except Exception as e:
        print(f"❌ Error reading CSV file: {e}")
        return False

def retry_failed_geocoding(failed_unis, university_data):
    """
    Retry geocoding for universities that failed the first time
    """
    print(f"\n🔄 Retrying geocoding for {len(failed_unis)} universities...")
    
    api_key = '18c9586b4d8940878bcd8018a0c93e59'
    base_url = 'https://api.opencagedata.com/geocode/v1/json'
    
    for i, university in enumerate(failed_unis):
        print(f"Retrying {i+1}/{len(failed_unis)}: {university}")
        
        # Try different search variations
        search_terms = [
            f"{university} university United States",
            f"{university} college United States",
            f"{university} campus United States",
            university.replace("-", " ") + " United States",
            university.split("-")[0] + " United States" if "-" in university else None
        ]
        
        # Remove None values
        search_terms = [term for term in search_terms if term]
        
        found = False
        for term in search_terms:
            if found:
                break
                
            params = {
                'q': term,
                'key': api_key,
                'limit': 1,
                'countrycode': 'us'
            }
            
            try:
                response = requests.get(base_url, params=params)
                response.raise_for_status()
                data = response.json()
                
                if data['results']:
                    result = data['results'][0]
                    latitude = result['geometry']['lat']
                    longitude = result['geometry']['lng']
                    formatted_address = result['formatted']
                    confidence = result.get('confidence', 0)
                    
                    # Extract state and city
                    state = None
                    city = None
                    if 'components' in result:
                        components = result['components']
                        state = components.get('state_code') or components.get('state')
                        city = components.get('city') or components.get('town') or components.get('village')
                    
                    # Update the university_data list
                    for j, row in enumerate(university_data):
                        if row[0] == university:
                            university_data[j] = [
                                university, latitude, longitude, 
                                formatted_address, state, city, confidence
                            ]
                            break
                    
                    print(f"  ✓ Found with '{term}': {latitude}, {longitude}")
                    found = True
                    break
                    
            except Exception as e:
                print(f"  ⚠️  Error with '{term}': {e}")
            
            time.sleep(1.1)  # Rate limiting
        
        if not found:
            print(f"  ✗ Still not found after retry")
    
    # Save updated results
    save_coordinates_to_csv(university_data, 'universities_coordinates_all_updated.csv')
    print_summary(university_data)

def main():
    """
    Main function to orchestrate the geocoding process
    """
    print("🗺️  GIS Master's Programs - University Geocoding Script")
    print("=" * 60)
    
    # Install chardet if not available
    try:
        import chardet
    except ImportError:
        print("📦 Installing chardet for encoding detection...")
        import subprocess
        import sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "chardet"])
        import chardet
    
    # Verify data integrity first
    if not verify_data_integrity():
        return
    
    # Get coordinates for all universities
    print(f"\n🔍 Starting geocoding process...")
    university_data = get_all_university_coordinates()
    
    if not university_data:
        print("❌ No data to process. Exiting.")
        return
    
    # Save to CSV
    print(f"\n💾 Saving results...")
    save_coordinates_to_csv(university_data)
    
    # Print summary
    print_summary(university_data)
    
    # Ask user if they want to retry failed geocoding
    failed_unis = [row[0] for row in university_data if row[1] is None]
    if failed_unis:
        print(f"\n🔄 Would you like to retry geocoding for {len(failed_unis)} failed universities?")
        print(f"   (This will try with modified search terms)")
        retry = input("   Enter 'y' to retry, or any other key to skip: ").lower().strip()
        
        if retry == 'y':
            retry_failed_geocoding(failed_unis, university_data)

if __name__ == "__main__":
    main() 