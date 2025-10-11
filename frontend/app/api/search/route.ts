import { NextRequest } from 'next/server';
import { getCloudflareContext } from '@opennextjs/cloudflare';
import { DATABASE_CONFIGS } from '../../config/databaseConfig';

export async function GET(request: NextRequest) {
  try {
    const { env } = getCloudflareContext();
    const { searchParams } = new URL(request.url);
    const query = searchParams.get('q') || '';

    if (!query || query.length < 2) {
      return Response.json({ 
        error: 'Search query must be at least 2 characters',
        results: []
      }, { status: 400 });
    }

    const searchTerm = `%${query}%`;
    const searchPromises = DATABASE_CONFIGS.map(async (dbConfig) => {
    if ((env as any)[dbConfig.key]) {
        try {
        const result = await (env as any)[dbConfig.key]
            .prepare('SELECT * FROM problems WHERE statement LIKE ? OR solution LIKE ? LIMIT 10')
            .bind(searchTerm, searchTerm)
            .all();
        
        return result.results.map((p: any) => ({ ...p, source: dbConfig.source }));
        } catch (e) {
        console.error(`${dbConfig.errorPrefix} search error:`, e);
        return [];
        }
    }
    return [];
    });

    const allResults = await Promise.all(searchPromises);
    const results = allResults.flat();

    return Response.json({ 
      success: true,
      results: results,
      count: results.length,
      query: query
    });
  } catch (error: any) {
    console.error('Search Error:', error);
    return Response.json({ 
      error: error.message,
      results: []
    }, { status: 500 });
  }
}
