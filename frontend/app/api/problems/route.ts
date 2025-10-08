import { NextRequest } from 'next/server';
import { getCloudflareContext } from '@opennextjs/cloudflare';

export async function GET(request: NextRequest) {
  try {
    const { env } = getCloudflareContext();
    
    const { searchParams } = new URL(request.url);
    const contest = searchParams.get('contest') || 'imo';
    
    let db: any;
    if (contest === 'imo') db = (env as any).IMO_DB;
    else if (contest === 'putnam') db = (env as any).PUTNAM_DB;
    else if (contest === 'mit') db = (env as any).MIT_DB;
    else {
      return Response.json({ error: 'Invalid contest' }, { status: 400 });
    }

    if (!db) {
      return Response.json({ error: `${contest} database not found` }, { status: 500 });
    }
    
    const result = await db.prepare('SELECT * FROM problems LIMIT 10').all();
    
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
