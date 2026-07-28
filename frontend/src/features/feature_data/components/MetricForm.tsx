import React, { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { CategoryHttpService, Metric } from "../services/CategoryHttpService";
import Loading from "core/components/Loading";
import Error from "core/components/Error";
import TagsWidget from "core/components/forms/TagsWidget";

interface MetricFormProps {
  onSubmit?: (metric: Metric) => void;
}

const MetricForm: React.FC<MetricFormProps> = ({ onSubmit }) => {
  const { categoryId, id } = useParams<{ categoryId: string; id: string }>();
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    tags: [] as string[],
  });

  useEffect(() => {
    if (id && id !== "new") {
      loadMetric();
    }
  }, [id]);

  const loadMetric = async () => {
    try {
      setIsLoading(true);
      const metrics = await CategoryHttpService.getCategoryMetrics(parseInt(categoryId!));
      const metric = metrics.find((m: Metric) => m.id === parseInt(id!));
      if (metric) {
        setFormData({
          name: metric.name,
          description: metric.description || "",
          tags: metric.tags,
        });
      }
    } catch (err) {
      setError("Failed to load metric");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setIsLoading(true);
      const metricData = {
        name: formData.name,
        description: formData.description,
        tags: formData.tags,
      };

      let metric: Metric;
      if (id && id !== "new") {
        metric = await CategoryHttpService.updateMetric(
          parseInt(categoryId!),
          parseInt(id),
          metricData
        );
      } else {
        metric = await CategoryHttpService.createMetric(
          parseInt(categoryId!),
          metricData
        );
      }

      if (onSubmit) {
        onSubmit(metric);
      } else {
        navigate(`/categories/${categoryId}`);
      }
    } catch (err) {
      setError("Failed to save metric");
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleTagsChange = (tags: string[]) => {
    setFormData(prev => ({ ...prev, tags }));
  };

  if (isLoading) return <Loading isLoading={isLoading} />;
  if (error) return <Error error={error} />;

  return (
    <form onSubmit={handleSubmit}>
      <div className="mb-3">
        <label htmlFor="name" className="form-label">Name</label>
        <input
          type="text"
          className="form-control"
          id="name"
          name="name"
          value={formData.name}
          onChange={handleChange}
          required
          placeholder="Enter metric name"
        />
      </div>

      <div className="mb-3">
        <label htmlFor="description" className="form-label">Description</label>
        <textarea
          className="form-control"
          id="description"
          name="description"
          value={formData.description}
          onChange={handleChange}
          rows={3}
          placeholder="Enter metric description"
        />
      </div>

      <div className="mb-3">
        <label className="form-label">Tags</label>
        {/* <TagsWidget
          tags={formData.tags}
          onChange={handleTagsChange}
        /> */}
      </div>

      <div className="d-flex gap-2">
        <button type="submit" className="btn btn-primary" disabled={isLoading}>
          {id && id !== "new" ? "Update" : "Create"}
        </button>
        <button
          type="button"
          className="btn btn-secondary"
          onClick={() => navigate(`/categories/${categoryId}`)}
        >
          Cancel
        </button>
      </div>
    </form>
  );
};

export default MetricForm; 