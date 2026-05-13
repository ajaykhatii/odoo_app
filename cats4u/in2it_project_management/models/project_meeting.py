# -*- encoding: utf-8 -*-
##############################################################################
#
#    In2IT Technologies Pvt. Ltd
#    Copyright (C) 2025 (https://www.in2ittech.com)
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError,UserError
from markupsafe import Markup
from datetime import datetime,timedelta, timezone
import pytz


class CalendarEvent(models.Model):
    _inherit = "calendar.event"

    project_id = fields.Many2one("project.project",string="Project")
    available_time = fields.Html("Available Time")
    case_id = fields.Many2one("crm.lead", string="Case")

    @api.constrains('start_date','start','attendee_ids','allday')
    def check_attendee_available(self):
        for rec in self:
            if rec.start:
                if rec.start < fields.Datetime.now():
                    raise ValidationError("You cannot schedule a meeting in the past. Please choose a future date and time.")
            if rec.start_date:
                if rec.start_date < fields.Date.today():
                    raise ValidationError("You cannot schedule a meeting in the past. Please choose a future date and time.")

            if rec.allday:
                # Full-day event → entire day range
                start_date = rec.start_date
                end_date = rec.stop_date or rec.start_date

                new_start = fields.Datetime.from_string(f"{start_date} 00:00:00")
                new_stop = fields.Datetime.from_string(f"{end_date} 23:59:59")
            else:
                if not rec.start or not rec.stop:
                    continue
                new_start = rec.start
                new_stop = rec.stop

            event = self.env['calendar.event'].search([('partner_ids', 'in', rec.partner_ids.ids),('id', '!=', rec.id),('start', '<', new_stop),('stop', '>', new_start)], limit=1)
            if event:
                raise ValidationError(f"Due to prior commitments, the chosen time slot is occupied. Please reschedule your meeting for another available time.")

    @api.onchange("partner_ids")
    def action_check_availability(self):
        MIN_SLOT_MINUTES = 10
        calendar = self.env['resource.calendar'].search([('company_id', '=', self.env.company.id)],order="id desc",limit=1)

        if not calendar:
            raise ValidationError("Please Configure the working schedule.")

        attendance_lines = calendar.attendance_ids.filtered(lambda a: a.day_period != 'lunch')

        if not attendance_lines:
            raise ValidationError("No working hours defined in the schedule.")

        working_day_time = sorted({(line.hour_from, line.hour_to) for line in attendance_lines},key=lambda x: x[0])

        for rec in self:
            date = rec.start_date if rec.allday else rec.start.date()

            common_available_slots = []
            partners = rec.partner_ids
            for shift in working_day_time:
                start_hour, end_hour = shift
                user_tz = pytz.timezone(self.env.user.tz or 'UTC')

                shift_start = datetime.combine(date, datetime.min.time()) + timedelta(
                    hours=int(start_hour),
                    minutes=int((start_hour % 1) * 60)
                )

                shift_end = datetime.combine(date, datetime.min.time()) + timedelta(
                    hours=int(end_hour),
                    minutes=int((end_hour % 1) * 60)
                )

                # Localize (attach user TZ)
                shift_start = user_tz.localize(shift_start)
                shift_end = user_tz.localize(shift_end)

                # Convert to UTC
                shift_start_utc = shift_start.astimezone(pytz.UTC).replace(tzinfo=None)
                shift_end_utc = shift_end.astimezone(pytz.UTC).replace(tzinfo=None)
                
                domain = [('start', '<', shift_end_utc),('stop', '>', shift_start_utc),('partner_ids', 'in', partners.ids)]

                meetings = self.env['calendar.event'].search(domain, order='start asc')
                free_start = shift_start_utc
                for meeting in meetings:

                    meeting_start = meeting.start
                    meeting_end = meeting.stop
                    if meeting_start > free_start:
                        duration = (meeting_start - free_start).total_seconds() / 60
                        if duration >= MIN_SLOT_MINUTES:
                            common_available_slots.append({
                                'start': free_start,
                                'end': meeting_start
                            })

                    free_start = max(free_start, meeting_end)

                # After last meeting
                if free_start < shift_end_utc:
                    duration = (shift_end_utc - free_start).total_seconds() / 60
                    if duration >= MIN_SLOT_MINUTES:
                        common_available_slots.append({
                            'start': free_start,
                            'end': shift_end_utc
                        })

            if not common_available_slots:
                raise ValidationError("No common available slot found!")

            result = "Available Time:<br/>"
            for slot in common_available_slots:
                start_utc = pytz.UTC.localize(slot['start'])
                end_utc = pytz.UTC.localize(slot['end'])

                # Convert to user timezone
                start_local = start_utc.astimezone(user_tz)
                end_local = end_utc.astimezone(user_tz)

                # Format nicely
                formatted_start = start_local.strftime("%Y-%m-%d %I:%M %p")
                formatted_end = end_local.strftime("%Y-%m-%d %I:%M %p")

                result += f"{formatted_start} - {formatted_end}<br/>\n"

            rec.available_time = result
