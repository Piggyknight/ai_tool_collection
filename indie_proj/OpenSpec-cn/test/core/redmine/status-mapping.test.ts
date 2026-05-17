/**
 * Unit tests for StatusMapper
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { StatusMapper, HERMES_STATES, BUG_STATES, DEFAULT_HERMES_STATUS_MAPPING, DEFAULT_BUG_STATUS_MAPPING } from '../../../src/core/redmine/status-mapping.js';

describe('StatusMapper', () => {
  let mapper: StatusMapper;

  beforeEach(() => {
    mapper = new StatusMapper();
  });

  describe('hermesToRedmine', () => {
    it('should map all Hermes states correctly', () => {
      expect(mapper.hermesToRedmine('plan')).toBe('Plan');
      expect(mapper.hermesToRedmine('propose')).toBe('Propose');
      expect(mapper.hermesToRedmine('applying')).toBe('Applying');
      expect(mapper.hermesToRedmine('done')).toBe('Done');
      expect(mapper.hermesToRedmine('code-review')).toBe('Code Review');
      expect(mapper.hermesToRedmine('testing')).toBe('Testing');
      expect(mapper.hermesToRedmine('archiving')).toBe('Archiving');
    });

    it('should return the mapped value for all valid states', () => {
      for (const state of HERMES_STATES) {
        const mapped = mapper.hermesToRedmine(state);
        expect(mapped).toBeDefined();
        expect(typeof mapped).toBe('string');
      }
    });
  });

  describe('bugToRedmine', () => {
    it('should map all bug states correctly', () => {
      expect(mapper.bugToRedmine('new')).toBe('待修复');
      expect(mapper.bugToRedmine('in-progress')).toBe('修复中');
      expect(mapper.bugToRedmine('fixed')).toBe('修复完成');
      expect(mapper.bugToRedmine('verified')).toBe('验证完成');
    });

    it('should return the mapped value for all valid bug states', () => {
      for (const state of BUG_STATES) {
        const mapped = mapper.bugToRedmine(state);
        expect(mapped).toBeDefined();
        expect(typeof mapped).toBe('string');
      }
    });
  });

  describe('customToRedmine', () => {
    it('should return undefined for unmapped custom states', () => {
      expect(mapper.customToRedmine('custom')).toBeUndefined();
    });

    it('should return mapped value for configured custom states', () => {
      const customMapper = new StatusMapper({ custom: { 'custom': 'Custom Status' } });
      expect(customMapper.customToRedmine('custom')).toBe('Custom Status');
    });
  });

  describe('openspecToHermes', () => {
    it('should map OpenSpec artifacts to Hermes states', () => {
      expect(mapper.openspecToHermes('proposal')).toBe('plan');
      expect(mapper.openspecToHermes('specs')).toBe('propose');
      expect(mapper.openspecToHermes('design')).toBe('propose');
      expect(mapper.openspecToHermes('tasks')).toBe('applying');
      expect(mapper.openspecToHermes('apply')).toBe('applying');
      expect(mapper.openspecToHermes('archive')).toBe('archiving');
    });

    it('should return undefined for unmapped artifacts', () => {
      expect(mapper.openspecToHermes('unknown')).toBeUndefined();
    });
  });

  describe('getHermesStates', () => {
    it('should return all Hermes states', () => {
      const states = mapper.getHermesStates();
      expect(states).toEqual(HERMES_STATES);
      expect(states).toHaveLength(7);
    });
  });

  describe('getBugStates', () => {
    it('should return all bug states', () => {
      const states = mapper.getBugStates();
      expect(states).toEqual(BUG_STATES);
      expect(states).toHaveLength(4);
    });
  });

  describe('getNextHermesState', () => {
    it('should return next state in workflow', () => {
      expect(mapper.getNextHermesState('plan')).toBe('propose');
      expect(mapper.getNextHermesState('propose')).toBe('applying');
      expect(mapper.getNextHermesState('applying')).toBe('done');
      expect(mapper.getNextHermesState('done')).toBe('code-review');
      expect(mapper.getNextHermesState('code-review')).toBe('testing');
      expect(mapper.getNextHermesState('testing')).toBe('archiving');
    });

    it('should return null for final state', () => {
      expect(mapper.getNextHermesState('archiving')).toBeNull();
    });
  });

  describe('getPreviousHermesState', () => {
    it('should return previous state in workflow', () => {
      expect(mapper.getPreviousHermesState('archiving')).toBe('testing');
      expect(mapper.getPreviousHermesState('testing')).toBe('code-review');
      expect(mapper.getPreviousHermesState('code-review')).toBe('done');
      expect(mapper.getPreviousHermesState('done')).toBe('applying');
      expect(mapper.getPreviousHermesState('applying')).toBe('propose');
      expect(mapper.getPreviousHermesState('propose')).toBe('plan');
    });

    it('should return null for initial state', () => {
      expect(mapper.getPreviousHermesState('plan')).toBeNull();
    });
  });

  describe('isHermesCompleted', () => {
    it('should identify completed states', () => {
      expect(mapper.isHermesCompleted('done')).toBe(true);
      expect(mapper.isHermesCompleted('testing')).toBe(true);
      expect(mapper.isHermesCompleted('archiving')).toBe(true);
    });

    it('should identify active states', () => {
      expect(mapper.isHermesCompleted('plan')).toBe(false);
      expect(mapper.isHermesCompleted('propose')).toBe(false);
      expect(mapper.isHermesCompleted('applying')).toBe(false);
      expect(mapper.isHermesCompleted('code-review')).toBe(false);
    });
  });

  describe('isHermesActive', () => {
    it('should identify active states', () => {
      expect(mapper.isHermesActive('plan')).toBe(true);
      expect(mapper.isHermesActive('propose')).toBe(true);
      expect(mapper.isHermesActive('applying')).toBe(true);
      expect(mapper.isHermesActive('code-review')).toBe(true);
    });

    it('should identify completed states as inactive', () => {
      expect(mapper.isHermesActive('done')).toBe(false);
      expect(mapper.isHermesActive('testing')).toBe(false);
      expect(mapper.isHermesActive('archiving')).toBe(false);
    });
  });

  describe('calculateProgress', () => {
    it('should calculate progress correctly', () => {
      expect(mapper.calculateProgress(0, 10)).toBe(0);
      expect(mapper.calculateProgress(5, 10)).toBe(50);
      expect(mapper.calculateProgress(10, 10)).toBe(100);
      expect(mapper.calculateProgress(3, 4)).toBe(75);
    });

    it('should handle zero total tasks', () => {
      expect(mapper.calculateProgress(5, 0)).toBe(0);
    });

    it('should round to integer', () => {
      expect(mapper.calculateProgress(1, 3)).toBe(33);
      expect(mapper.calculateProgress(2, 3)).toBe(67);
    });
  });

  describe('getStateFromProgress', () => {
    it('should return done for 100% progress', () => {
      expect(mapper.getStateFromProgress(100, 'plan')).toBe('done');
    });

    it('should return applying for progress > 0 and < 100', () => {
      expect(mapper.getStateFromProgress(50, 'plan')).toBe('applying');
      expect(mapper.getStateFromProgress(1, 'plan')).toBe('applying');
    });

    it('should respect current task state for special states', () => {
      expect(mapper.getStateFromProgress(0, 'code-review')).toBe('code-review');
      expect(mapper.getStateFromProgress(0, 'testing')).toBe('testing');
    });

    it('should default to propose for zero progress', () => {
      expect(mapper.getStateFromProgress(0, 'plan')).toBe('propose');
    });
  });

  describe('isValidRedmineStatus', () => {
    it('should validate Hermes status names', () => {
      expect(mapper.isValidRedmineStatus('Plan')).toBe(true);
      expect(mapper.isValidRedmineStatus('Done')).toBe(true);
      expect(mapper.isValidRedmineStatus('Testing')).toBe(true);
    });

    it('should validate Bug status names', () => {
      expect(mapper.isValidRedmineStatus('待修复')).toBe(true);
      expect(mapper.isValidRedmineStatus('修复中')).toBe(true);
      expect(mapper.isValidRedmineStatus('验证完成')).toBe(true);
    });

    it('should validate custom status names', () => {
      const customMapper = new StatusMapper({ custom: { 'custom': 'Custom Status' } });
      expect(customMapper.isValidRedmineStatus('Custom Status')).toBe(true);
    });

    it('should reject unknown status names', () => {
      expect(mapper.isValidRedmineStatus('Unknown')).toBe(false);
      expect(mapper.isValidRedmineStatus('Invalid')).toBe(false);
    });
  });

  describe('Custom Configuration', () => {
    it('should accept custom Hermes status mapping', () => {
      const customMapper = new StatusMapper({ hermes: { 'plan': 'Planning Phase' } });
      expect(customMapper.hermesToRedmine('plan')).toBe('Planning Phase');
    });

    it('should accept custom Bug status mapping', () => {
      const customMapper = new StatusMapper({ bug: { 'new': 'New Bug' } });
      expect(customMapper.bugToRedmine('new')).toBe('New Bug');
    });

    it('should merge custom with defaults', () => {
      const customMapper = new StatusMapper({ hermes: { 'plan': 'Planning Phase' } });
      expect(customMapper.hermesToRedmine('plan')).toBe('Planning Phase');
      expect(customMapper.hermesToRedmine('done')).toBe('Done'); // Default preserved
    });
  });
});

describe('Constants', () => {
  describe('HERMES_STATES', () => {
    it('should have 7 states', () => {
      expect(HERMES_STATES).toHaveLength(7);
    });

    it('should contain all expected states', () => {
      expect(HERMES_STATES).toContain('plan');
      expect(HERMES_STATES).toContain('propose');
      expect(HERMES_STATES).toContain('applying');
      expect(HERMES_STATES).toContain('done');
      expect(HERMES_STATES).toContain('code-review');
      expect(HERMES_STATES).toContain('testing');
      expect(HERMES_STATES).toContain('archiving');
    });
  });

  describe('BUG_STATES', () => {
    it('should have 4 states', () => {
      expect(BUG_STATES).toHaveLength(4);
    });

    it('should contain all expected states', () => {
      expect(BUG_STATES).toContain('new');
      expect(BUG_STATES).toContain('in-progress');
      expect(BUG_STATES).toContain('fixed');
      expect(BUG_STATES).toContain('verified');
    });
  });

  describe('DEFAULT_HERMES_STATUS_MAPPING', () => {
    it('should map all Hermes states', () => {
      expect(Object.keys(DEFAULT_HERMES_STATUS_MAPPING)).toHaveLength(7);
      for (const state of HERMES_STATES) {
        expect(DEFAULT_HERMES_STATUS_MAPPING[state]).toBeDefined();
      }
    });
  });

  describe('DEFAULT_BUG_STATUS_MAPPING', () => {
    it('should map all Bug states', () => {
      expect(Object.keys(DEFAULT_BUG_STATUS_MAPPING)).toHaveLength(4);
      for (const state of BUG_STATES) {
        expect(DEFAULT_BUG_STATUS_MAPPING[state]).toBeDefined();
      }
    });
  });
});