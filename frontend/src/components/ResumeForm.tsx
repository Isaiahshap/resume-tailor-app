import React, { useState } from 'react';
import { 
  Container, 
  TextField, 
  Button, 
  Paper, 
  Typography,
  Box,
  CircularProgress,
  Alert,
  Snackbar
} from '@mui/material';
import axios from 'axios';
import { FormData } from '../index';

const DEFAULT_PROMPT = "Create a professional resume that highlights my relevant experience for this position. Focus on technical achievements and leadership experience.";

const ResumeForm: React.FC = () => {
  const [formData, setFormData] = useState<FormData>({
    experience: '',
    job_description: '',
    prompt: DEFAULT_PROMPT,
    loading: false,
    error: null
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.experience.trim() || !formData.job_description.trim()) {
      setFormData(prev => ({ 
        ...prev, 
        error: 'Please fill in all required fields' 
      }));
      return;
    }

    setFormData(prev => ({ ...prev, loading: true, error: null }));

    try {
      const response = await axios.post(
        'http://localhost:8001/generate_pdf',
        {
          experience: formData.experience.trim(),
          job_description: formData.job_description.trim(),
          prompt: formData.prompt.trim() || DEFAULT_PROMPT
        },
        {
          responseType: 'blob',
          timeout: 30000 // 30 second timeout
        }
      );

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'tailored-resume.pdf');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url); // Clean up the URL object
    } catch (error) {
      let errorMessage = 'Error generating resume. Please try again.';
      if (axios.isAxiosError(error) && error.code === 'ECONNABORTED') {
        errorMessage = 'Request timed out. Please try again.';
      }
      setFormData(prev => ({ ...prev, error: errorMessage }));
    } finally {
      setFormData(prev => ({ ...prev, loading: false }));
    }
  };

  return (
    <Container maxWidth="md">
      <Paper elevation={3} sx={{ p: 4, mt: 4 }}>
        <Typography variant="h4" gutterBottom>
          Resume Generator
        </Typography>
        
        <form onSubmit={handleSubmit}>
          <TextField
            fullWidth
            label="Your Experience"
            name="experience"
            value={formData.experience}
            onChange={handleChange}
            multiline
            rows={4}
            margin="normal"
            placeholder="Senior Software Engineer at TechCorp (2020-Present)"
            required
          />

          <TextField
            fullWidth
            label="Job Description"
            name="job_description"
            value={formData.job_description}
            onChange={handleChange}
            multiline
            rows={4}
            margin="normal"
            placeholder="Paste the job description here..."
            required
          />

          <TextField
            fullWidth
            label="Custom Prompt (optional)"
            name="prompt"
            value={formData.prompt}
            onChange={handleChange}
            multiline
            rows={2}
            margin="normal"
          />

          <Box sx={{ mt: 2 }}>
            <Button 
              variant="contained" 
              color="primary" 
              type="submit"
              disabled={formData.loading}
              fullWidth
            >
              {formData.loading ? (
                <CircularProgress size={24} color="inherit" />
              ) : (
                'Generate Resume PDF'
              )}
            </Button>
          </Box>
        </form>

        <Snackbar 
          open={!!formData.error} 
          autoHideDuration={6000} 
          onClose={() => setFormData(prev => ({ ...prev, error: null }))}
        >
          <Alert severity="error">{formData.error}</Alert>
        </Snackbar>
      </Paper>
    </Container>
  );
};

export default ResumeForm;