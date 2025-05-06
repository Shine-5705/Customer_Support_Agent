const axios = require('axios');
const cheerio = require('cheerio');
const fs = require('fs');
const pdfParse = require('pdf-parse');

const baseURL = 'https://www.drdo.gov.in';
const startURL = baseURL + '/drdo/';
const visited = new Set();
const output = [];

function cleanTextFromHTML($) {
  $('header, footer, nav, script, style').remove();
  const text = $('body').text();
  return text.replace(/\s+/g, ' ').replace(/&nbsp;/g, ' ').trim();
}

async function fetchPDFText(url) {
  try {
    console.log(`📄 Fetching PDF: ${url}`);
    const response = await axios.get(url, { responseType: 'arraybuffer' });
    const data = await pdfParse(response.data);
    return data.text.replace(/\s+/g, ' ').trim();
  } catch (err) {
    console.error(`❌ PDF Failed: ${url}`);
    return '';
  }
}

async function crawl(url) {
  if (visited.has(url) || !url.startsWith(baseURL)) return;
  visited.add(url);
  console.log(`🔍 Crawling: ${url}`);

  try {
    const { data } = await axios.get(url);
    const $ = cheerio.load(data);
    const textContent = cleanTextFromHTML($);

    const pageInfo = {
      url,
      content: textContent,
      pdfs: [],
      links: []
    };

    // Find PDF links
    $('a[href$=".pdf"]').each((_, el) => {
      const href = $(el).attr('href');
      if (!href) return;
      const fullPDF = href.startsWith('http') ? href : baseURL + href;
      pageInfo.pdfs.push(fullPDF);
    });

    // Find internal links
    const internalLinks = $('a[href]')
      .map((_, el) => $(el).attr('href'))
      .get()
      .filter(href => href && (href.startsWith(baseURL) || href.startsWith('/')))
      .map(link => (link.startsWith('/') ? baseURL + link : link));

    pageInfo.links = internalLinks;

    output.push(pageInfo);

    // Crawl deeper into the site
    for (const link of internalLinks) {
      await crawl(link);
    }

    // Process each PDF on the page
    for (const pdfURL of pageInfo.pdfs) {
      const pdfText = await fetchPDFText(pdfURL);
      output.push({
        url: pdfURL,
        content: pdfText,
        pdf: true
      });
    }

  } catch (err) {
    console.error(`❌ Failed to crawl ${url}: ${err.message}`);
  }
}

(async () => {
  if (!fs.existsSync('output')) fs.mkdirSync('output');
  await crawl(startURL);
  fs.writeFileSync('output/drdo_scraped.json', JSON.stringify(output, null, 2));
  console.log(`✅ Finished! Scraped ${output.length} entries.`);
})(); 