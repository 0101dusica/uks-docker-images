-- Example: Initial SQL for PostgreSQL
-- This script runs only on first container startup (when database is empty)
-- Add your custom initialization here

-- CREATE DATABASE mydb;
-- CREATE USER myuser WITH ENCRYPTED PASSWORD 'mypassword';
-- GRANT ALL PRIVILEGES ON DATABASE mydb TO myuser;

/*INSERT INTO public.repositories_repository
(name, description, visibility, is_official, stars, created_at, updated_at, owner_id)
VALUES
-- Official images (owner_id = 1 → "docker" org for example)
('nginx', 'Official build of Nginx web server.', 'public', true, 120000, NOW() - INTERVAL '2000 days', NOW() - INTERVAL '1 days', 1),
('redis', 'In-memory data structure store, used as a database, cache, and message broker.', 'public', true, 98000, NOW() - INTERVAL '1900 days', NOW() - INTERVAL '1 days', 1),
('postgres', 'The PostgreSQL object-relational database system.', 'public', true, 87000, NOW() - INTERVAL '1800 days', NOW() - INTERVAL '2 days', 1),
('node', 'Node.js JavaScript runtime.', 'public', true, 110000, NOW() - INTERVAL '1700 days', NOW() - INTERVAL '1 days', 1),
('python', 'Python programming language image.', 'public', true, 95000, NOW() - INTERVAL '1600 days', NOW() - INTERVAL '1 days', 1),

-- Verified publisher (owner_id = 2 → company/org)
('mysql', 'MySQL is a widely used relational database management system.', 'public', true, 76000, NOW() - INTERVAL '1500 days', NOW() - INTERVAL '3 days', 2),
('mongo', 'MongoDB document database.', 'public', true, 72000, NOW() - INTERVAL '1400 days', NOW() - INTERVAL '2 days', 2),
('rabbitmq', 'Message broker software that implements AMQP.', 'public', true, 45000, NOW() - INTERVAL '1300 days', NOW() - INTERVAL '5 days', 2),

-- Popular community images (owner_id = 3,4...)
('frontend-app', 'Production-ready React frontend served with Nginx.', 'public', false, 5400, NOW() - INTERVAL '300 days', NOW() - INTERVAL '2 days', 3),
('backend-api', 'Django REST API containerized with Docker.', 'public', false, 3200, NOW() - INTERVAL '280 days', NOW() - INTERVAL '4 days', 3),
('dev-environment', 'Full-stack dev environment with Docker Compose.', 'public', false, 2100, NOW() - INTERVAL '250 days', NOW() - INTERVAL '3 days', 4),

-- Smaller personal repos
('portfolio-site', 'Personal website container.', 'public', false, 120, NOW() - INTERVAL '90 days', NOW() - INTERVAL '1 days', 5),
('chat-server', 'WebSocket-based chat backend.', 'public', false, 85, NOW() - INTERVAL '60 days', NOW() - INTERVAL '2 days', 5),
('test-image', 'Testing Docker builds and CI pipelines.', 'private', false, 5, NOW() - INTERVAL '20 days', NOW() - INTERVAL '1 days', 6);
*/