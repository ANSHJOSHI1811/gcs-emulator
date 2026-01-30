import {
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Box,
  Typography,
} from '@mui/material';
import { useProjectStore } from '@/stores/projectStore';

// Common GCP projects for testing
const PROJECTS = [
  { id: 'test-project', name: 'Test Project' },
  { id: 'demo-project', name: 'Demo Project' },
  { id: 'dev-project', name: 'Development Project' },
  { id: 'prod-project', name: 'Production Project' },
];

export default function ProjectSelector() {
  const { selectedProject, setSelectedProject } = useProjectStore();

  return (
    <Box sx={{ minWidth: 200 }}>
      <FormControl size="small" fullWidth variant="outlined">
        <InputLabel id="project-selector-label">Project</InputLabel>
        <Select
          labelId="project-selector-label"
          id="project-selector"
          value={selectedProject || ''}
          label="Project"
          onChange={(e) => setSelectedProject(e.target.value)}
          sx={{ bgcolor: 'background.paper' }}
        >
          {PROJECTS.map((project) => (
            <MenuItem key={project.id} value={project.id}>
              <Box>
                <Typography variant="body2">{project.name}</Typography>
                <Typography variant="caption" color="text.secondary">
                  {project.id}
                </Typography>
              </Box>
            </MenuItem>
          ))}
        </Select>
      </FormControl>
    </Box>
  );
}
