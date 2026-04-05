import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, RefreshControl, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';

export default function AnalyticsScreen() {
  const [complaints, setComplaints] = useState<any[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [filter, setFilter] = useState<string | null>(null);

  useEffect(() => {
    loadComplaints();
  }, [filter]);

  const loadComplaints = async () => {
    try {
      const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;
      const sessionToken = await AsyncStorage.getItem('session_token');
      
      let url = BACKEND_URL + '/api/complaints?limit=50';
      if (filter) {
        url += '&risk_level=' + filter;
      }

      const response = await fetch(url, {
        headers: {
          'Authorization': 'Bearer ' + sessionToken,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setComplaints(data);
      }
    } catch (error) {
      console.error('Load complaints error:', error);
    } finally {
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadComplaints();
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <Text style={styles.title}>Analytics</Text>
        <Text style={styles.subtitle}>Complaint analysis and insights</Text>
      </View>

      <ScrollView
        horizontal
        style={styles.filterContainer}
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.filterContent}
      >
        <FilterChip label="All" active={filter === null} onPress={() => setFilter(null)} />
        <FilterChip label="Low Risk" active={filter === 'Low'} onPress={() => setFilter('Low')} />
        <FilterChip label="Medium Risk" active={filter === 'Medium'} onPress={() => setFilter('Medium')} />
        <FilterChip label="High Risk" active={filter === 'High'} onPress={() => setFilter('High')} />
      </ScrollView>

      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#3B82F6" />
        }
      >
        {complaints.map((complaint, index) => (
          <ComplaintCard key={index} complaint={complaint} />
        ))}
        {complaints.length === 0 && (
          <View style={styles.emptyState}>
            <Ionicons name="analytics-outline" size={64} color="#64748b" />
            <Text style={styles.emptyText}>No complaints found</Text>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

function FilterChip({ label, active, onPress }: any) {
  return (
    <TouchableOpacity
      style={[styles.filterChip, active && styles.filterChipActive]}
      onPress={onPress}
    >
      <Text style={[styles.filterChipText, active && styles.filterChipTextActive]}>
        {label}
      </Text>
    </TouchableOpacity>
  );
}

function ComplaintCard({ complaint }: any) {
  const prediction = complaint.prediction;
  const riskScore = prediction?.risk_score || 0;
  const isAnomaly = prediction?.is_anomaly || false;

  return (
    <View style={styles.card}>
      <View style={styles.cardHeader}>
        <Text style={styles.cardId}>{complaint.complaint_id}</Text>
        {isAnomaly && (
          <View style={styles.anomalyBadge}>
            <Text style={styles.anomalyText}>ANOMALY</Text>
          </View>
        )}
      </View>
      
      <Text style={styles.cardType}>{complaint.complaint_type}</Text>
      <Text style={styles.cardLocation}>{complaint.location}</Text>
      <Text style={styles.cardDescription} numberOfLines={2}>
        {complaint.description}
      </Text>
      
      <View style={styles.cardFooter}>
        <View style={styles.riskIndicator}>
          <Text style={styles.riskLabel}>Risk Score</Text>
          <View style={[styles.riskBar, { width: Math.min(riskScore, 100) + '%', backgroundColor: getRiskColor(riskScore) }]} />
          <Text style={styles.riskScore}>{riskScore.toFixed(0)}%</Text>
        </View>
        <Text style={styles.cardStatus}>{complaint.status}</Text>
      </View>
    </View>
  );
}

function getRiskColor(score: number) {
  if (score >= 70) return '#EF4444';
  if (score >= 40) return '#F59E0B';
  return '#10B981';
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0c0c0c',
  },
  header: {
    padding: 16,
    paddingTop: 8,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#fff',
  },
  subtitle: {
    fontSize: 14,
    color: '#94a3b8',
    marginTop: 4,
  },
  filterContainer: {
    maxHeight: 60,
  },
  filterContent: {
    paddingHorizontal: 16,
    gap: 8,
  },
  filterChip: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#1a1a2e',
    borderWidth: 1,
    borderColor: '#2d3748',
  },
  filterChipActive: {
    backgroundColor: '#3B82F6',
    borderColor: '#3B82F6',
  },
  filterChipText: {
    fontSize: 14,
    color: '#94a3b8',
  },
  filterChipTextActive: {
    color: '#fff',
    fontWeight: '600',
  },
  scrollView: {
    flex: 1,
    padding: 16,
  },
  card: {
    backgroundColor: '#1a1a2e',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    gap: 8,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  cardId: {
    fontSize: 12,
    color: '#64748b',
    fontFamily: 'monospace',
  },
  anomalyBadge: {
    backgroundColor: '#F59E0B',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  anomalyText: {
    fontSize: 10,
    fontWeight: 'bold',
    color: '#fff',
  },
  cardType: {
    fontSize: 18,
    fontWeight: '600',
    color: '#fff',
  },
  cardLocation: {
    fontSize: 14,
    color: '#94a3b8',
  },
  cardDescription: {
    fontSize: 14,
    color: '#cbd5e1',
    marginTop: 4,
  },
  cardFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 8,
  },
  riskIndicator: {
    flex: 1,
    gap: 4,
  },
  riskLabel: {
    fontSize: 12,
    color: '#64748b',
  },
  riskBar: {
    height: 6,
    borderRadius: 3,
  },
  riskScore: {
    fontSize: 12,
    fontWeight: '600',
    color: '#fff',
  },
  cardStatus: {
    fontSize: 12,
    color: '#3B82F6',
    textTransform: 'uppercase',
    fontWeight: '600',
  },
  emptyState: {
    alignItems: 'center',
    justifyContent: 'center',
    padding: 32,
    gap: 16,
  },
  emptyText: {
    fontSize: 16,
    color: '#64748b',
  },
});
