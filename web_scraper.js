const puppeteer = require('puppeteer');
const axios = require('axios');
const cheerio = require('cheerio');
const fs = require('fs');

const visited = new Set();
const baseURL = 'https://www.drdo.gov.in';
const output = [];

async function crawl(url) {
  if (visited.has(url) || !url.startsWith(baseURL)) return;
  visited.add(url);

  try {
    const { data } = await axios.get(url);
    const $ = cheerio.load(data);
    const textContent = $('body').text().replace(/\s+/g, ' ').trim();

    output.push({
      url,
      content: textContent
    });

    const links = $('a[href]').map((_, el) => $(el).attr('href')).get();

    for (let link of links) {
      if (link.startsWith('/')) link = baseURL + link;
      await crawl(link);
    }
  } catch (err) {
    console.error(`Failed to crawl ${url}:`, err.message);
  }
}

(async () => {
  await crawl(baseURL + '/drdo/');
  fs.writeFileSync('drdo_scraped.json', JSON.stringify(output, null, 2));
  console.log(`Scraped ${output.length} pages.`);
})();
