/**
 * Protocol form/detail component registry.
 *
 * Provides dynamic component resolution based on device protocol type.
 * Each protocol can have a custom form component for create/edit and
 * a custom detail component for the device detail page.
 *
 * If no custom component exists for a protocol, null is returned and
 * the caller falls back to the generic protocol config form built from
 * PROTOCOL_CONFIGS.
 */
import { computed, defineComponent, h, watch, type Component, type PropType } from 'vue'
import { NButton, NForm, NFormItem, NInput, NInputNumber, NSelect, NSwitch, NDivider, NText, type FormInst } from 'naive-ui'
import { PROTOCOL_CONFIGS } from '@/constants/protocolConfig'
import type { ProtocolFieldDef } from '@/constants/protocolConfig'
import { t } from '@/i18n'

/**
 * Generic protocol form component that renders config fields + point
 * definition editor based on PROTOCOL_CONFIGS.
 * Used as fallback when no protocol-specific component exists.
 *
 * FIXED-P0: 原实现与 DeviceList 创建/编辑向导的调用约定不匹配，导致 UI 创建
 * 设备 100% 失败（console: "protocolFormRef.value?.validate is not a function"，
 * toast 只显示“操作失败”，POST 请求根本不会发出）：
 *   1. 未实现 validate()/getAssembledConfig()/getAssembledPoints()，
 *      onCreateClick/onEditClick 调用即抛 TypeError；
 *   2. 字段编辑写 modelValue，但父组件传的是 config，输入内容从不回流；
 *   3. 不渲染测点定义区，points 恒为 []，即使发出请求也会被后端
 *      PointDef min_length=1 门禁 422 拒绝。
 * 现按调用约定实现三件套接口；字段直接写回父组件 reactive config 引用；
 * 测点区在创建模式下默认预填协议模板（可增删改），必填/格式/范围前端校验；
 * 校验错误附带 userMessage 供 extractError 直接展示给用户。
 */
const GenericProtocolForm = defineComponent({
  name: 'GenericProtocolForm',
  props: {
    protocol: { type: String, required: true },
    config: { type: Object, default: () => ({}) },
    points: { type: Array as PropType<Record<string, any>[]>, default: () => [] },
    mode: { type: String, default: 'create' },
    driverSchemas: { type: Object, default: () => ({}) },
    disabled: { type: Boolean, default: false },
  },
  setup(props, { expose }) {
    const configs = PROTOCOL_CONFIGS
    const cfg = computed(() => configs.value[props.protocol])

    const DATA_TYPE_OPTIONS = ['bool', 'int16', 'int32', 'uint16', 'uint32', 'float32', 'float64', 'string'].map(v => ({ label: v, value: v }))
    const ACCESS_MODE_OPTIONS = [
      { label: 'r', value: 'r' }, { label: 'rw', value: 'rw' }, { label: 'w', value: 'w' },
    ]

    // FIXED-P0: 直接写回父组件传入的 reactive config 引用（原实现写 modelValue，
    // 父组件传的是 config，编辑内容从不回流）
    const setField = (key: string, v: any) => {
      props.config[key] = v
    }

    function blankPoint(): Record<string, any> {
      return { name: '', data_type: 'float32', unit: '', address: '0', access_mode: 'r', min: null, max: null, mode: null }
    }

    // 创建模式下默认预填协议测点模板，协议切换时重置（减少手动录入）；
    // 编辑模式不动已有测点
    // FIXED-P0: PROTOCOL_CONFIGS 模板使用 'read'/'rw' 等展示值，而后端 PointDef
    // access_mode 仅接受 Literal["r","w","rw"]，data_type 仅接受 8 种标量类型；
    // 直接透传模板值会被后端 422 拒绝（UI 创建设备必失败，用户只能用脚本加设备）。
    // 现统一归一化：access_mode 映射到 r/w/rw，非法 data_type 降级为 string。
    const _ACCESS_MODE_MAP: Record<string, string> = {
      read: 'r', write: 'w', read_write: 'rw', readwrite: 'rw', rw: 'rw', r: 'r', w: 'w',
    }
    const _VALID_DATA_TYPES = new Set(['bool', 'int16', 'int32', 'uint16', 'uint32', 'float32', 'float64', 'string'])
    function fillTemplatePoints() {
      if (props.mode !== 'create') return
      props.points.splice(0, props.points.length)
      for (const tpl of cfg.value?.pointTemplates || []) {
        const am = _ACCESS_MODE_MAP[String(tpl.access_mode ?? tpl.access ?? 'r')] || 'r'
        const dt = _VALID_DATA_TYPES.has(tpl.data_type) ? tpl.data_type : 'string'
        props.points.push({
          name: tpl.name, data_type: dt, unit: tpl.unit || '',
          address: tpl.address || '0', access_mode: am,
          min: null, max: null, mode: null,
        })
      }
    }
    watch(() => props.protocol, fillTemplatePoints, { immediate: true })

    function _userError(msg: string): Error {
      const err = new Error(msg)
      ;(err as any).userMessage = msg
      return err
    }

    /**
     * 校验配置与测点；通过则返回组装后的 config（调用方 merge 进 createForm.config），
     * 失败抛带 userMessage 的 Error。
     */
    function validate(): Record<string, any> {
      const c = cfg.value
      if (!c) return { ...props.config }
      const invalid: string[] = []
      for (const f of c.configFields) {
        if (f.notImplemented) continue
        const v = props.config?.[f.key] ?? f.default
        const empty = v === undefined || v === null || String(v).trim() === ''
        if (empty) {
          if (f.required) invalid.push(f.label)
          continue
        }
        if (f.pattern && !new RegExp(f.pattern).test(String(v))) invalid.push(f.label)
        else if (f.type === 'number') {
          const n = Number(v)
          if (Number.isNaN(n) || (f.min !== undefined && n < f.min) || (f.max !== undefined && n > f.max)) invalid.push(f.label)
        }
      }
      if (invalid.length) throw _userError(`${t('deviceList.fillRequiredFields')}: ${invalid.join(' / ')}`)
      if (props.points.length === 0) throw _userError(t('deviceList.needAtLeastOnePoint'))
      for (const p of props.points) {
        if (!String(p.name || '').trim() || String(p.address ?? '').trim() === '') {
          throw _userError(t('deviceList.pointNameAddrRequired'))
        }
      }
      return { ...props.config }
    }

    function getAssembledConfig(): Record<string, any> {
      return { ...props.config }
    }

    function getAssembledPoints(): Record<string, any>[] {
      return JSON.parse(JSON.stringify(props.points))
    }

    // FIXED-P0: 必须显式 expose，否则父组件 protocolFormRef 拿不到这三个方法，
    // onCreateClick 调 validate() 直接 TypeError（“操作失败”的根因之一）
    expose({ validate, getAssembledConfig, getAssembledPoints })

    return () => {
      const c = cfg.value
      if (!c) return null
      const fieldNodes = c.configFields.map((field: ProtocolFieldDef) => {
        const value = props.config?.[field.key] ?? field.default
        if (field.notImplemented) {
          return h(NFormItem, { label: field.label }, {
            default: () => h(NText, { depth: 3, italic: true }, { default: () => field.tooltip || 'Not implemented' }),
          })
        }
        if (field.type === 'number') {
          return h(NFormItem, { label: field.label, required: field.required }, {
            default: () => h(NInputNumber, {
              value,
              disabled: props.disabled,
              placeholder: field.placeholder,
              min: field.min,
              max: field.max,
              'onUpdate:value': (v: number | null) => setField(field.key, v),
            }),
          })
        }
        if (field.type === 'boolean') {
          return h(NFormItem, { label: field.label }, {
            default: () => h(NSwitch, {
              value,
              disabled: props.disabled,
              'onUpdate:value': (v: boolean) => setField(field.key, v),
            }),
          })
        }
        if (field.type === 'select') {
          return h(NFormItem, { label: field.label, required: field.required }, {
            default: () => h(NSelect, {
              value,
              disabled: props.disabled,
              options: field.options || [],
              'onUpdate:value': (v: any) => setField(field.key, v),
            }),
          })
        }
        if (field.type === 'password') {
          return h(NFormItem, { label: field.label, required: field.required }, {
            default: () => h(NInput, {
              value,
              type: 'password',
              showPasswordOn: 'click',
              disabled: props.disabled,
              placeholder: field.placeholder,
              'onUpdate:value': (v: string) => setField(field.key, v),
            }),
          })
        }
        return h(NFormItem, { label: field.label, required: field.required }, {
          default: () => h(NInput, {
            value,
            disabled: props.disabled,
            placeholder: field.placeholder,
            'onUpdate:value': (v: string) => setField(field.key, v),
          }),
        })
      })
      const pointRows = props.points.map((pt, idx) => h('div', { key: idx, style: 'display:flex;gap:6px;align-items:center;padding:3px 0;flex-wrap:wrap' }, [
        h(NInput, { value: pt.name, placeholder: t('deviceList.pointName'), size: 'small', style: 'width:130px', 'onUpdate:value': (v: string) => { pt.name = v } }),
        h(NInput, { value: pt.address, placeholder: 'HR_0', size: 'small', style: 'width:90px', 'onUpdate:value': (v: string) => { pt.address = v } }),
        h(NSelect, { value: pt.data_type, options: DATA_TYPE_OPTIONS, size: 'small', style: 'width:105px', 'onUpdate:value': (v: string) => { pt.data_type = v } }),
        h(NInput, { value: pt.unit, placeholder: t('deviceList.unit'), size: 'small', style: 'width:70px', 'onUpdate:value': (v: string) => { pt.unit = v } }),
        h(NSelect, { value: pt.access_mode || 'r', options: ACCESS_MODE_OPTIONS, size: 'small', style: 'width:78px', 'onUpdate:value': (v: string) => { pt.access_mode = v } }),
        h(NInputNumber, { value: pt.min, placeholder: t('deviceList.min'), size: 'small', style: 'width:100px', 'onUpdate:value': (v: number | null) => { pt.min = v } }),
        h(NInputNumber, { value: pt.max, placeholder: t('deviceList.max'), size: 'small', style: 'width:100px', 'onUpdate:value': (v: number | null) => { pt.max = v } }),
        h(NButton, { text: true, type: 'error', size: 'small', onClick: () => props.points.splice(idx, 1) }, { default: () => t('common.delete') }),
      ]))
      return h('div', { class: 'protocol-form-generic' }, [
        h(NDivider, { titlePlacement: 'left' }, { default: () => c.label }),
        ...fieldNodes,
        h(NDivider, { titlePlacement: 'left' }, { default: () => t('deviceList.pointDefinition') }),
        ...(pointRows.length ? pointRows : [h(NText, { depth: 3 }, { default: () => t('deviceList.needAtLeastOnePoint') })]),
        h(NButton, { dashed: true, block: true, size: 'small', style: 'margin-top:6px', onClick: () => props.points.push(blankPoint()) }, { default: () => t('deviceList.addPoint') }),
      ])
    }
  },
})

/**
 * Generic protocol detail component for the device detail page.
 */
const GenericProtocolDetail = defineComponent({
  name: 'GenericProtocolDetail',
  props: {
    protocol: { type: String, required: true },
    config: { type: Object, default: () => ({}) },
    device: { type: Object, default: () => ({}) },
  },
  setup(props) {
    const configs = PROTOCOL_CONFIGS
    return () => {
      const cfg = configs.value[props.protocol]
      if (!cfg) return null
      return h('div', { class: 'protocol-detail-generic' }, [
        h(NDivider, { titlePlacement: 'left' }, { default: () => cfg.label }),
        ...cfg.configFields.map((field: ProtocolFieldDef) => {
          const value = props.config?.[field.key] ?? field.default
          return h('div', { key: field.key, style: 'display:flex;justify-content:space-between;padding:4px 0;' }, [
            h('span', { style: 'color:var(--text-color-3);' }, field.label + ':'),
            h('span', null, String(value ?? '-')),
          ])
        }),
      ])
    }
  },
})

// Registry of protocol-specific components (can be extended)
const _formRegistry: Record<string, Component> = {}
const _detailRegistry: Record<string, Component> = {}

/**
 * Get the protocol-specific form component for create/edit dialogs.
 * Returns null if no specific component exists (caller should use generic form).
 */
export function getProtocolFormComponent(protocol: string): Component | null {
  return _formRegistry[protocol] || GenericProtocolForm
}

/**
 * Get the protocol-specific detail component for the device detail page.
 * Returns null if no specific component exists (caller should use generic detail).
 */
export function getProtocolDetailComponent(protocol: string): Component | null {
  return _detailRegistry[protocol] || GenericProtocolDetail
}

/**
 * Register a custom protocol form component.
 */
export function registerProtocolFormComponent(protocol: string, component: Component): void {
  _formRegistry[protocol] = component
}

/**
 * Register a custom protocol detail component.
 */
export function registerProtocolDetailComponent(protocol: string, component: Component): void {
  _detailRegistry[protocol] = component
}
