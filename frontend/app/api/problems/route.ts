import { NextRequest } from 'next/server';
import { getCloudflareContext } from '@opennextjs/cloudflare';
import { DATABASE_CONFIGS } from '../../config/databaseConfig';

export async function GET(request: NextRequest) {
  try {
    const { env } = getCloudflareContext();
    
    const { searchParams } = new URL(request.url);
    const contest = searchParams.get('contest') || 'imo';
    
    let db: any;
    const db_names = DATABASE_CONFIGS.map(config => config.source);
    if (db_names.includes(contest)) {
      db = (env as any)[DATABASE_CONFIGS.find(config => config.source === contest)?.key || ''];
    }
    else {
      return Response.json({ error: 'Invalid contest' }, { status: 400 });
    }

    if (!db) {
      return Response.json({ error: `${contest} database not found` }, { status: 500 });
    }
    
    const result = await db.prepare('SELECT * FROM problems').all();
    
    return Response.json({ 
      success: true,
      problems: result.results,
      count: result.results.length 
    });
  } catch (error: any) {
    console.error('API Error:', error);
    return Response.json({ 
      error: 'Database query failed',
      message: error.message 
    }, { status: 500 });
  }
}
