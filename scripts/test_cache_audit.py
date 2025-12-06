# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
"""
Test script for cache and audit services
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.cache_service import CacheService
from src.services.audit import AuditLogger, AuditRecord

def test_cache():
    """Test cache service"""
    print("=" * 60)
    print("Testing Cache Service")
    print("=" * 60)
    
    cache = CacheService("data/app.db")
    
    # Test 1: Set and get user cache
    print("\n1. Testing user cache...")
    cache.set_user_answer("user1", "Qual a pauta?", "Pauta da 3ª reunião...")
    answer = cache.get_user_answer("user1", "Qual a pauta?")
    assert answer == "Pauta da 3ª reunião...", "User cache failed"
    print("   ✅ User cache works")
    
    # Test 2: Normalization
    print("\n2. Testing normalization...")
    answer2 = cache.get_user_answer("user1", "QUAL A PAUTA??")
    assert answer2 == answer, "Normalization failed"
    print("   ✅ Normalization works (case-insensitive)")
    
    # Test 3: Global cache
    print("\n3. Testing global cache...")
    cache.set_global_answer("Qual o regimento?", "Regimento do CONSUNI...")
    answer3 = cache.get_global_answer("Qual o regimento?")
    assert answer3 == "Regimento do CONSUNI...", "Global cache failed"
    print("   ✅ Global cache works")
    
    # Test 4: Negative bypass
    print("\n4. Testing negative answer bypass...")
    negative = "Não encontrei informações sobre isso."
    should_bypass = cache.should_bypass_cache(negative)
    assert should_bypass == True, "Negative bypass failed"
    print("   ✅ Negative bypass works")
    
    # Test 5: Stats
    print("\n5. Testing stats...")
    stats = cache.get_stats()
    print(f"   Cache stats: {stats}")
    assert stats['user_cache_entries'] >= 1, "Stats failed"
    print("   ✅ Stats work")
    
    print("\n" + "=" * 60)
    print("✅ All cache tests passed!")
    print("=" * 60)

def test_audit():
    """Test audit service"""
    print("\n" + "=" * 60)
    print("Testing Audit Service")
    print("=" * 60)
    
    audit = AuditLogger("data/app.db")
    
    # Test 1: Log interaction
    print("\n1. Testing audit logging...")
    audit.log(AuditRecord(
        user="user1",
        role="publico",
        input_text="Teste de pergunta",
        output_text="Teste de resposta",
        metadata={"test": True}
    ))
    print("   ✅ Audit logging works")
    
    # Test 2: List recent
    print("\n2. Testing list recent...")
    records = audit.list_recent(limit=1)
    assert len(records) >= 1, "List recent failed"
    assert records[0].input_text == "Teste de pergunta", "Record content mismatch"
    print(f"   ✅ List recent works (found {len(records)} records)")
    
    # Test 3: Stats
    print("\n3. Testing stats...")
    stats = audit.get_stats()
    print(f"   Audit stats: {stats}")
    assert stats['total_interactions'] >= 1, "Stats failed"
    print("   ✅ Stats work")
    
    # Test 4: Search
    print("\n4. Testing search...")
    results = audit.search("Teste", limit=5)
    assert len(results) >= 1, "Search failed"
    print(f"   ✅ Search works (found {len(results)} results)")
    
    print("\n" + "=" * 60)
    print("✅ All audit tests passed!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_cache()
        test_audit()
        print("\n🎉 ALL TESTS PASSED! 🎉\n")
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
