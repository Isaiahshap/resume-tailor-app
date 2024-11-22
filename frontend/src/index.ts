export interface ResumeRequest {
    experience: string;
    job_description: string;
    prompt: string;
  }
  
  export interface FormData extends ResumeRequest {
    loading: boolean;
    error: string | null;
  }