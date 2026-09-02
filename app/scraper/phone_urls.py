# Curated, individually-verified list of GSMArena spec-page URLs.
#
# GSMArena's search/listing endpoints (results.php3) sit behind a Cloudflare
# Turnstile challenge and cannot be scraped with plain requests, so this static
# list (verified by fetching each page and checking its <h1> title) is used
# instead of crawling a listing/search page.
PHONE_URLS: dict[str, str] = {
    "Samsung Galaxy S21": "https://www.gsmarena.com/samsung_galaxy_s21-10693.php",
    "Samsung Galaxy S21+ 5G": "https://www.gsmarena.com/samsung_galaxy_s21+_5g-10625.php",
    "Samsung Galaxy S21 Ultra 5G": "https://www.gsmarena.com/samsung_galaxy_s21_ultra_5g-10596.php",
    "Samsung Galaxy S22 5G": "https://www.gsmarena.com/samsung_galaxy_s22_5g-11253.php",
    "Samsung Galaxy S22+ 5G": "https://www.gsmarena.com/samsung_galaxy_s22+_5g-11252.php",
    "Samsung Galaxy S22 Ultra 5G": "https://www.gsmarena.com/samsung_galaxy_s22_ultra_5g-11251.php",
    "Samsung Galaxy S23": "https://www.gsmarena.com/samsung_galaxy_s23-12082.php",
    "Samsung Galaxy S23+": "https://www.gsmarena.com/samsung_galaxy_s23+-12083.php",
    "Samsung Galaxy S23 Ultra": "https://www.gsmarena.com/samsung_galaxy_s23_ultra-12024.php",
    "Samsung Galaxy S24": "https://www.gsmarena.com/samsung_galaxy_s24-12773.php",
    "Samsung Galaxy S24+": "https://www.gsmarena.com/samsung_galaxy_s24+-12772.php",
    "Samsung Galaxy S24 Ultra": "https://www.gsmarena.com/samsung_galaxy_s24_ultra-12771.php",
    "Samsung Galaxy Z Flip5": "https://www.gsmarena.com/samsung_galaxy_z_flip5-12252.php",
    "Samsung Galaxy Z Fold5": "https://www.gsmarena.com/samsung_galaxy_z_fold5-12418.php",
    "Samsung Galaxy A54": "https://www.gsmarena.com/samsung_galaxy_a54-12070.php",
}
