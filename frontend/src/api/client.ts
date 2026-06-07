import axios from 'axios';

const client = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
});

export interface Review {
  id: string;
  repo_full_name: string;
  pr_number: number;
  pr_title: string | null;
  pr_author: string | null;
  status: string;
  diff_summary: string | null;
  findings: Finding[] | null;
  error: string | null;
  total_comments: number;
  created_at: string | null;
  completed_at: string | null;
}

export interface Finding {
  severity: 'critical' | 'major' | 'minor';
  category: 'bug' | 'security' | 'quality' | 'performance' | 'style';
  file: string;
  line: number;
  message: string;
  suggestion: string;
}

export interface ReviewListResponse {
  reviews: Review[];
  total: number;
}

export async function getReviews(page = 1, limit = 20): Promise<ReviewListResponse> {
  const { data } = await client.get('/reviews', { params: { page, limit } });
  return data;
}

export async function getReview(id: string): Promise<Review> {
  const { data } = await client.get(`/reviews/${id}`);
  return data;
}

export async function getHealth(): Promise<{ status: string }> {
  const { data } = await client.get('/health');
  return data;
}
