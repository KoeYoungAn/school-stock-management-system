import React from 'react'
import MasterDataPage from './_MasterDataPage.jsx'
import { required, minLength } from '../utils/validation.js'

const departmentSchema = {
  department_name: [required('Department Name'), minLength(2, 'Department Name')]
}

export default function Departments() {
  return <MasterDataPage
    base="/api/departments" title={{ key:'department', newKey:'newDepartment', editKey:'editDepartment', emptyKey:'noDepartments' }} nameKey="department_name"
    blankForm={{ department_name:'', department_head:'', room_code:'', location:'', status:'Active', notes:'' }}
    fields={[
      { name:'department_name', labelKey:'departmentName', required:true },
      { name:'department_head', labelKey:'departmentHead' },
      { name:'room_code', labelKey:'roomCode' },
      { name:'location', labelKey:'location' },
      { name:'status', labelKey:'status', type:'select', options:['Active','Inactive'] },
      { name:'notes', labelKey:'notes', type:'textarea' },
    ]}
    columns={[
      { key:'department_name', labelKey:'name' },
      { key:'department_head', labelKey:'head' },
      { key:'room_code', labelKey:'room' },
      { key:'location', labelKey:'location' },
    ]}
    validationSchema={departmentSchema}
  />
}
