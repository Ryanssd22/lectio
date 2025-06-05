import { execFile } from 'child_process';
import { promisify } from 'util';
import path from 'path';

const execFileAsync = promisify(execFile);

export async function GET() {
	const scriptPath = path.resolve('src/scripts/generateLiturgy.py');
	try {
		const { stdout } = await execFileAsync('python3', [scriptPath]);
		return new Response(JSON.stringify({ output: stdout }), {
			headers: { 'Content-Type': 'application/json' }
		});
	} catch (error) {
		return new Response(JSON.stringify({ error: error.message }), { status: 500 });
	}
}
