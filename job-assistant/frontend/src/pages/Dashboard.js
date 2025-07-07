import React from 'react';
import { useQuery } from 'react-query';
import {
  BriefcaseIcon,
  DocumentTextIcon,
  PaperAirplaneIcon,
  UsersIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';

// Mock API calls - replace with actual API
const fetchDashboardData = async () => {
  // This would be replaced with actual API call
  return {
    stats: {
      totalJobs: 45,
      totalApplications: 12,
      hrContacts: 8,
      pendingApplications: 3,
    },
    recentJobs: [
      {
        id: 1,
        title: 'Senior Frontend Developer',
        company: 'TechCorp',
        location: 'Москва',
        matchScore: 92,
        addedAt: '2024-01-15T10:00:00Z',
      },
      {
        id: 2,
        title: 'React Developer',
        company: 'StartupXYZ',
        location: 'Санкт-Петербург',
        matchScore: 88,
        addedAt: '2024-01-15T09:30:00Z',
      },
    ],
    recentApplications: [
      {
        id: 1,
        jobTitle: 'Frontend Developer',
        company: 'DevCompany',
        status: 'sent',
        appliedAt: '2024-01-14T14:00:00Z',
      },
      {
        id: 2,
        jobTitle: 'React Developer',
        company: 'WebStudio',
        status: 'pending',
        appliedAt: '2024-01-14T12:00:00Z',
      },
    ],
  };
};

const StatCard = ({ title, value, icon: Icon, color = 'primary' }) => {
  const colorClasses = {
    primary: 'bg-primary-50 text-primary-600',
    success: 'bg-success-50 text-success-600',
    warning: 'bg-warning-50 text-warning-600',
    danger: 'bg-danger-50 text-danger-600',
  };

  return (
    <div className="card">
      <div className="flex items-center">
        <div className={`p-3 rounded-lg ${colorClasses[color]}`}>
          <Icon className="h-6 w-6" />
        </div>
        <div className="ml-4">
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-semibold text-gray-900">{value}</p>
        </div>
      </div>
    </div>
  );
};

const JobCard = ({ job }) => (
  <div className="border rounded-lg p-4 hover:bg-gray-50 transition-colors">
    <div className="flex justify-between items-start">
      <div className="flex-1">
        <h4 className="font-medium text-gray-900">{job.title}</h4>
        <p className="text-sm text-gray-600">{job.company}</p>
        <p className="text-xs text-gray-500">{job.location}</p>
      </div>
      <div className="text-right">
        <span className="badge badge-success">{job.matchScore}% совпадение</span>
        <p className="text-xs text-gray-500 mt-1">
          {new Date(job.addedAt).toLocaleDateString('ru-RU')}
        </p>
      </div>
    </div>
  </div>
);

const ApplicationCard = ({ application }) => {
  const statusConfig = {
    sent: { label: 'Отправлено', color: 'success' },
    pending: { label: 'В ожидании', color: 'warning' },
    rejected: { label: 'Отклонено', color: 'danger' },
    interview: { label: 'Собеседование', color: 'info' },
  };

  const status = statusConfig[application.status] || statusConfig.pending;

  return (
    <div className="border rounded-lg p-4">
      <div className="flex justify-between items-start">
        <div>
          <h4 className="font-medium text-gray-900">{application.jobTitle}</h4>
          <p className="text-sm text-gray-600">{application.company}</p>
        </div>
        <div className="text-right">
          <span className={`badge badge-${status.color}`}>{status.label}</span>
          <p className="text-xs text-gray-500 mt-1">
            {new Date(application.appliedAt).toLocaleDateString('ru-RU')}
          </p>
        </div>
      </div>
    </div>
  );
};

export default function Dashboard() {
  const { data, isLoading, error } = useQuery('dashboard', fetchDashboardData);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <ExclamationTriangleIcon className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">Ошибка загрузки</h3>
        <p className="mt-1 text-sm text-gray-500">
          Не удалось загрузить данные дашборда
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Дашборд</h1>
        <p className="mt-1 text-sm text-gray-600">
          Обзор вашей активности по поиску работы
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Найдено вакансий"
          value={data?.stats.totalJobs || 0}
          icon={BriefcaseIcon}
          color="primary"
        />
        <StatCard
          title="Подано заявок"
          value={data?.stats.totalApplications || 0}
          icon={PaperAirplaneIcon}
          color="success"
        />
        <StatCard
          title="HR-контактов"
          value={data?.stats.hrContacts || 0}
          icon={UsersIcon}
          color="warning"
        />
        <StatCard
          title="Ожидают ответа"
          value={data?.stats.pendingApplications || 0}
          icon={ClockIcon}
          color="danger"
        />
      </div>

      {/* Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Recent Jobs */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-medium text-gray-900">
              Последние найденные вакансии
            </h3>
          </div>
          <div className="space-y-4">
            {data?.recentJobs?.length > 0 ? (
              data.recentJobs.map((job) => (
                <JobCard key={job.id} job={job} />
              ))
            ) : (
              <div className="text-center py-6">
                <BriefcaseIcon className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">
                  Вакансии не найдены
                </h3>
                <p className="mt-1 text-sm text-gray-500">
                  Настройте параметры поиска для начала работы
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Recent Applications */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-medium text-gray-900">
              Последние заявки
            </h3>
          </div>
          <div className="space-y-4">
            {data?.recentApplications?.length > 0 ? (
              data.recentApplications.map((application) => (
                <ApplicationCard key={application.id} application={application} />
              ))
            ) : (
              <div className="text-center py-6">
                <PaperAirplaneIcon className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">
                  Заявки не отправлены
                </h3>
                <p className="mt-1 text-sm text-gray-500">
                  Выберите интересные вакансии для подачи заявок
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-medium text-gray-900">Быстрые действия</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button className="btn-primary flex items-center justify-center">
            <DocumentTextIcon className="h-5 w-5 mr-2" />
            Обновить резюме
          </button>
          <button className="btn-secondary flex items-center justify-center">
            <BriefcaseIcon className="h-5 w-5 mr-2" />
            Найти вакансии
          </button>
          <button className="btn-secondary flex items-center justify-center">
            <UsersIcon className="h-5 w-5 mr-2" />
            Связаться с HR
          </button>
        </div>
      </div>
    </div>
  );
}