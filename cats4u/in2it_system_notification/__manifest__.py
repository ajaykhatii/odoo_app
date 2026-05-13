{
    'name': 'In2IT System Notification',
    'version': '18.0.1.0',
    'depends': ['base', 'mail'],
    'license': 'LGPL-3',
    "category": "Custom",
    "data": [
        "security/ir.model.access.csv",
        "data/notification_sequence.xml",
        "views/enquiry_views.xml"
    ],
    'assets':{
        'web.assets_backend': [
            "in2it_system_notification/static/src/js/systray_icon.js",
            'in2it_system_notification/static/src/xml/systray_icon.xml',
            "in2it_system_notification/static/src/js/systemNotificationService.js",
            "in2it_system_notification/static/src/css/systrayNotification.css",
            "in2it_system_notification/static/src/js/hide_chat_icon.js",
        ],
    },
    "installable": True,
    "application": True,
}
