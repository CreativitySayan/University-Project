import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, RefreshControl, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../../contexts/AuthContext';
import { useRouter } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface DashboardStats {
  total_complaints: number;
  high_risk_count: number;
  anomaly_count: number;
  alerts_count: number;
  risk_distribution: Record<string, number>;
  category_counts: Record<string, number>;
}

export default function DashboardScreen() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;
      const sessionToken = await AsyncStorage.getItem('session_token');
      
      const response = await fetch(BACKEND_URL + '/api/dashboard/stats', {
        headers: {
          'Authorization': 'Bearer ' + sessionToken,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Load stats error:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadStats();
  };

  const handleGenerateMockData = async () => {
    try {
      const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;
      const sessionToken = await AsyncStorage.getItem('session_token');
      
      const response = await fetch(BACKEND_URL + '/api/generate-mock-data?count=100', {
        method: 'POST',
        headers: {
          'Authorization': 'Bearer ' + sessionToken,
        },
      });

      if (response.ok) {
        loadStats();
      }
    } catch (error) {
      console.error('Generate mock data error:', error);
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#3B82F6" />
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#3B82F6" />
        }
      >
        <View style={styles.header}>
          <View>
            <Text style={styles.greeting}>Welcome back,</Text>
            <Text style={styles.userName}>{user?.name}</Text>
            <Text style={styles.roleTag}>{user?.role?.toUpperCase()}</Text>
          </View>
          <TouchableOpacity onPress={logout}>
            <Ionicons name="log-out-outline" size={24} color="#fff" />
          </TouchableOpacity>
        </View>

        <View style={styles.statsGrid}>
          <StatCard
            icon="document-text"
            label="Total Complaints"
            value={stats?.total_complaints || 0}
            color="#3B82F6"
          />
          <StatCard
            icon="warning"
            label="High Risk"
            value={stats?.high_risk_count || 0}
            color="#EF4444"
          />
          <StatCard
            icon="alert-circle"
            label="Anomalies"
            value={stats?.anomaly_count || 0}
            color="#F59E0B"
          />
          <StatCard
            icon="notifications"
            label="Active Alerts"
            value={stats?.alerts_count || 0}
            color="#10B981"
          />
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Risk Distribution</Text>
          <View style={styles.riskCards}>
            {stats?.risk_distribution && Object.entries(stats.risk_distribution).map(([level, count]) => (
              <View key={level} style={[styles.riskCard, getRiskStyle(level)]}>
                <Text style={styles.riskLevel}>{level}</Text>
                <Text style={styles.riskCount}>{count}</Text>
              </View>
            ))}
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Top Categories</Text>
          {stats?.category_counts && Object.entries(stats.category_counts).map(([category, count]) => (
            <View key={category} style={styles.categoryItem}>
              <Text style={styles.categoryName}>{category}</Text>
              <Text style={styles.categoryCount}>{count}</Text>
            </View>
          ))}
        </View>

        {(user?.role === 'admin' || user?.role === 'analyst') && (
          <TouchableOpacity style={styles.mockButton} onPress={handleGenerateMockData}>
            <Ionicons name="flask" size={20} color="#fff" />
            <Text style={styles.mockButtonText}>Generate Mock Data (100 records)</Text>
          </TouchableOpacity>
        )}

        <View style={{ height: 24 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

function StatCard({ icon, label, value, color }: any) {
  return (
    <View style={[styles.statCard, { borderLeftColor: color }]}>
      <Ionicons name={icon} size={32} color={color} />
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

function getRiskStyle(level: string) {
  switch (level) {
    case 'Low':
      return { backgroundColor: 'rgba(16, 185, 129, 0.2)', borderColor: '#10B981' };
    case 'Medium':
      return { backgroundColor: 'rgba(245, 158, 11, 0.2)', borderColor: '#F59E0B' };
    case 'High':
      return { backgroundColor: 'rgba(239, 68, 68, 0.2)', borderColor: '#EF4444' };
    default:
      return {};
  }
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0c0c0c',
  },
  loadingContainer: {
    flex: 1,
    backgroundColor: '#0c0c0c',
    alignItems: 'center',
    justifyContent: 'center',
  },
  scrollView: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    paddingTop: 8,
  },
  greeting: {
    fontSize: 14,
    color: '#94a3b8',
  },
  userName: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
    marginTop: 4,
  },
  roleTag: {
    fontSize: 12,
    color: '#3B82F6',
    marginTop: 4,
    fontWeight: '600',
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    padding: 8,
    gap: 8,
  },
  statCard: {
    width: '48%',
    backgroundColor: '#1a1a2e',
    padding: 16,
    borderRadius: 12,
    borderLeftWidth: 4,
    gap: 8,
  },
  statValue: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#fff',
  },
  statLabel: {
    fontSize: 12,
    color: '#94a3b8',
  },
  section: {
    padding: 16,
    gap: 12,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#fff',
  },
  riskCards: {
    flexDirection: 'row',
    gap: 8,
  },
  riskCard: {
    flex: 1,
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    alignItems: 'center',
  },
  riskLevel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#fff',
  },
  riskCount: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
    marginTop: 4,
  },
  categoryItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    backgroundColor: '#1a1a2e',
    padding: 16,
    borderRadius: 8,
  },
  categoryName: {
    fontSize: 16,
    color: '#fff',
  },
  categoryCount: {
    fontSize: 16,
    fontWeight: '600',
    color: '#3B82F6',
  },
  mockButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#3B82F6',
    margin: 16,
    padding: 16,
    borderRadius: 12,
    gap: 8,
  },
  mockButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
});
