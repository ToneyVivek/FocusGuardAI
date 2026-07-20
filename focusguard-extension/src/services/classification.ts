/**
 * Website Classification Service for FocusGuard Extension
 * Rule-based website categorization
 */

import { logger } from '../utils/logger';
import { extractDomain } from '../utils/url';
import type { WebsiteCategory } from '../types/session';

/**
 * Domain classification rules
 * Maps domains to categories
 */
const DOMAIN_RULES: Record<string, WebsiteCategory> = {
  // DEVELOPMENT
  'github.com': 'DEVELOPMENT',
  'gitlab.com': 'DEVELOPMENT',
  'leetcode.com': 'DEVELOPMENT',
  'stackoverflow.com': 'DEVELOPMENT',
  'takeuforward.org': 'DEVELOPMENT',
  'programiz.com': 'DEVELOPMENT',
  'dev.to': 'DEVELOPMENT',
  'codepen.io': 'DEVELOPMENT',
  'replit.com': 'DEVELOPMENT',
  'codesandbox.io': 'DEVELOPMENT',
  'bitbucket.org': 'DEVELOPMENT',
  'npmjs.com': 'DEVELOPMENT',
  'pypi.org': 'DEVELOPMENT',
  'rust-lang.org': 'DEVELOPMENT',
  'go.dev': 'DEVELOPMENT',
  'kubernetes.io': 'DEVELOPMENT',
  'docker.com': 'DEVELOPMENT',
  'mongodb.com': 'DEVELOPMENT',
  'redis.io': 'DEVELOPMENT',
  'postgresql.org': 'DEVELOPMENT',
  'mysql.com': 'DEVELOPMENT',
  
  // ENTERTAINMENT
  'youtube.com': 'ENTERTAINMENT',
  'netflix.com': 'ENTERTAINMENT',
  'spotify.com': 'ENTERTAINMENT',
  'twitch.tv': 'ENTERTAINMENT',
  'soundcloud.com': 'ENTERTAINMENT',
  'hulu.com': 'ENTERTAINMENT',
  'disneyplus.com': 'ENTERTAINMENT',
  'hbo.com': 'ENTERTAINMENT',
  'primevideo.com': 'ENTERTAINMENT',
  'vimeo.com': 'ENTERTAINMENT',
  'dailymotion.com': 'ENTERTAINMENT',
  
  // SOCIAL_MEDIA
  'facebook.com': 'SOCIAL_MEDIA',
  'instagram.com': 'SOCIAL_MEDIA',
  'reddit.com': 'SOCIAL_MEDIA',
  'twitter.com': 'SOCIAL_MEDIA',
  'x.com': 'SOCIAL_MEDIA',
  'linkedin.com': 'SOCIAL_MEDIA',
  'pinterest.com': 'SOCIAL_MEDIA',
  'snapchat.com': 'SOCIAL_MEDIA',
  'tiktok.com': 'SOCIAL_MEDIA',
  'whatsapp.com': 'SOCIAL_MEDIA',
  'telegram.org': 'SOCIAL_MEDIA',
  'medium.com': 'SOCIAL_MEDIA',
  
  // COMMUNICATION
  'gmail.com': 'COMMUNICATION',
  'outlook.com': 'COMMUNICATION',
  'slack.com': 'COMMUNICATION',
  'discord.com': 'COMMUNICATION',
  'zoom.us': 'COMMUNICATION',
  'teams.microsoft.com': 'COMMUNICATION',
  'skype.com': 'COMMUNICATION',
  'meet.google.com': 'COMMUNICATION',
  'web.telegram.org': 'COMMUNICATION',
  'signal.org': 'COMMUNICATION',
  
  // SEARCH
  'google.com': 'SEARCH',
  'google.co.in': 'SEARCH',
  'bing.com': 'SEARCH',
  'duckduckgo.com': 'SEARCH',
  'yahoo.com': 'SEARCH',
  'baidu.com': 'SEARCH',
  'yandex.com': 'SEARCH',
  'ask.com': 'SEARCH',
  'ecosia.org': 'SEARCH',
  
  // SHOPPING
  'amazon.com': 'SHOPPING',
  'amazon.in': 'SHOPPING',
  'flipkart.com': 'SHOPPING',
  'ebay.com': 'SHOPPING',
  'etsy.com': 'SHOPPING',
  'walmart.com': 'SHOPPING',
  'target.com': 'SHOPPING',
  'bestbuy.com': 'SHOPPING',
  'shopify.com': 'SHOPPING',
  'aliexpress.com': 'SHOPPING',
  'alibaba.com': 'SHOPPING',
  
  // EDUCATION
  'coursera.org': 'EDUCATION',
  'udemy.com': 'EDUCATION',
  'wikipedia.org': 'EDUCATION',
  'khanacademy.org': 'EDUCATION',
  'edx.org': 'EDUCATION',
  'pluralsight.com': 'EDUCATION',
  'skillshare.com': 'EDUCATION',
  'udacity.com': 'EDUCATION',
  'mit.edu': 'EDUCATION',
  'stanford.edu': 'EDUCATION',
  'harvard.edu': 'EDUCATION',
  
  // PRODUCTIVITY
  'chat.openai.com': 'PRODUCTIVITY',
  'docs.google.com': 'PRODUCTIVITY',
  'notion.so': 'PRODUCTIVITY',
  'trello.com': 'PRODUCTIVITY',
  'asana.com': 'PRODUCTIVITY',
  'monday.com': 'PRODUCTIVITY',
  'figma.com': 'PRODUCTIVITY',
  'canva.com': 'PRODUCTIVITY',
  'evernote.com': 'PRODUCTIVITY',
  'dropbox.com': 'PRODUCTIVITY',
  'onedrive.live.com': 'PRODUCTIVITY',
  'drive.google.com': 'PRODUCTIVITY',
  'sheets.google.com': 'PRODUCTIVITY',
  'slides.google.com': 'PRODUCTIVITY',
  
  // NEWS
  'cnn.com': 'NEWS',
  'bbc.com': 'NEWS',
  'nytimes.com': 'NEWS',
  'theguardian.com': 'NEWS',
  'reuters.com': 'NEWS',
  'apnews.com': 'NEWS',
  'washingtonpost.com': 'NEWS',
  'wsj.com': 'NEWS',
  'bloomberg.com': 'NEWS',
  'ft.com': 'NEWS',
};

/**
 * Website Classification Service
 */
class ClassificationService {
  /**
   * Classify a URL into a category
   */
  classify(url: string | null): WebsiteCategory {
    if (!url) {
      return 'OTHER';
    }

    const domain = extractDomain(url);
    if (!domain) {
      return 'OTHER';
    }

    // Check exact domain match
    if (domain in DOMAIN_RULES) {
      const category = DOMAIN_RULES[domain];
      logger.info(`[CLASSIFICATION] Domain matched - Domain: ${domain}, Category: ${category}`);
      return category;
    }

    // Check subdomain match (e.g., docs.google.com -> google.com)
    const parts = domain.split('.');
    if (parts.length >= 2) {
      const baseDomain = parts.slice(-2).join('.');
      if (baseDomain in DOMAIN_RULES) {
        const category = DOMAIN_RULES[baseDomain];
        logger.info(`[CLASSIFICATION] Base domain matched - Base domain: ${baseDomain}, Category: ${category}`);
        return category;
      }
    }

    logger.info(`[CLASSIFICATION] No match found - Domain: ${domain}, Category: OTHER`);
    return 'OTHER';
  }

  /**
   * Get all available categories
   */
  getCategories(): WebsiteCategory[] {
    return [
      'DEVELOPMENT',
      'PRODUCTIVITY',
      'SOCIAL_MEDIA',
      'ENTERTAINMENT',
      'COMMUNICATION',
      'SHOPPING',
      'NEWS',
      'EDUCATION',
      'SEARCH',
      'OTHER',
    ];
  }
}

/**
 * Singleton classification service instance
 */
export const classificationService = new ClassificationService();
